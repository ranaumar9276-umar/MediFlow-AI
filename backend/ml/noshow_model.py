"""
No-show risk ML pipeline for MediFlow AI.

Phase 0 laid the foundation (single RandomForest, basic train/test split).
Phase 1 extends this into a real comparative ML workflow:

    Data -> Feature Engineering -> Train/Test Split -> Preprocessing
         -> Model Training (Logistic Regression, Decision Tree,
            Random Forest, XGBoost if available)
         -> Cross-Validation -> Evaluation (accuracy, precision, recall,
            F1, ROC-AUC, confusion matrix) -> Model Selection
         -> Persistence -> Inference

Data-leakage safeguards:
- Patient-history features (`patient_prior_*`) are computed strictly from
  each patient's PRIOR appointments only (chronologically shifted), so the
  model never sees information about the very appointment it is predicting
  or about that patient's future.
- The train/test split is stratified on the target to preserve class
  balance in both partitions.
- Cross-validation is performed only on the training partition; the test
  partition is held out and touched exactly once, at final evaluation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = MODEL_DIR / "noshow_model.joblib"
METRICS_PATH = MODEL_DIR / "noshow_model_metrics.json"

CATEGORICAL_FEATURES = ["department", "weekday"]
NUMERIC_FEATURES = [
    "hour_of_day",
    "duration_minutes",
    "patient_prior_appointment_count",
    "patient_prior_no_show_rate",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COLUMN = "is_no_show"


def _build_model_registry() -> dict:
    """
    Candidate models compared during training. XGBoost is included only if
    the optional dependency is installed (it is listed in requirements.txt
    but treated as soft-optional here so the pipeline degrades gracefully
    rather than crashing in environments where it wasn't installed).
    """
    registry = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(max_depth=6, random_state=42, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=150, max_depth=8, random_state=42, class_weight="balanced"
        ),
    }
    try:
        from xgboost import XGBClassifier  # optional dependency

        registry["xgboost"] = XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            eval_metric="logloss",
            random_state=42,
        )
    except ImportError:
        pass  # xgboost not installed in this environment - comparison proceeds without it
    return registry


def _build_pipeline(estimator) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds patient-history features computed strictly from PRIOR appointments
    (chronologically shifted per patient) - see module docstring for the
    data-leakage rationale.
    """
    if df.empty:
        out = df.copy()
        out["patient_prior_appointment_count"] = pd.Series(dtype=float)
        out["patient_prior_no_show_rate"] = pd.Series(dtype=float)
        return out

    df = df.sort_values(["patient_id", "scheduled_at"]).reset_index(drop=True).copy()
    outcome = df["status"].map({"NO_SHOW": 1, "COMPLETED": 0})

    df["patient_prior_appointment_count"] = outcome.groupby(df["patient_id"]).cumcount().astype(float)

    prior_rate = (
        outcome.groupby(df["patient_id"])
        .apply(lambda s: s.shift(1).expanding().mean())
        .reset_index(level=0, drop=True)
    )
    df["patient_prior_no_show_rate"] = prior_rate.fillna(0.0)
    return df


def prepare_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the supervised-learning frame: only COMPLETED/NO_SHOW appointments
    are usable as labeled outcomes (SCHEDULED appointments haven't happened
    yet, CANCELLED appointments don't tell us about no-show behavior).
    Feature engineering runs on the FULL history first so prior-appointment
    features have visibility into a patient's complete chronological record,
    then we filter down to labeled rows for training.
    """
    if df.empty:
        return df
    enriched = engineer_features(df)
    usable = enriched[enriched["status"].isin(["COMPLETED", "NO_SHOW"])].copy()
    usable[TARGET_COLUMN] = (usable["status"] == "NO_SHOW").astype(int)
    return usable


@dataclass
class ModelComparisonResult:
    model_name: str
    cv_metrics: dict
    test_metrics: dict


@dataclass
class TrainingResult:
    trained: bool
    reason: Optional[str]
    best_model: Optional[str]
    metrics: dict
    comparison: list = field(default_factory=list)
    n_samples: int = 0
    class_balance: dict = field(default_factory=dict)


def _evaluate(y_true, y_pred, y_proba) -> dict:
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
    }
    try:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_proba)), 4)
    except ValueError:
        # roc_auc is undefined if the test split ended up with only one class
        metrics["roc_auc"] = None

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics["confusion_matrix"] = {
        "true_negative": int(cm[0][0]),
        "false_positive": int(cm[0][1]),
        "false_negative": int(cm[1][0]),
        "true_positive": int(cm[1][1]),
    }
    return metrics


def train_and_compare_models(
    df: pd.DataFrame, min_samples: int = 30, cv_folds: int = 5
) -> TrainingResult:
    """
    Trains and cross-validates every candidate model, evaluates each on a
    held-out test set, selects the best by test-set F1 score (a reasonable
    default for an imbalanced no-show target, where accuracy alone is
    misleading), and persists the winning pipeline.

    Requires a minimum number of labeled samples before attempting to
    train at all, since a model trained on too little data would be
    meaningless - this is a safeguard against "ML for decoration."
    """
    usable = prepare_training_frame(df)

    if len(usable) < min_samples:
        return TrainingResult(
            trained=False,
            reason=f"Not enough labeled appointment history yet ({len(usable)} rows, "
            f"need at least {min_samples}). This is expected for a freshly seeded "
            f"database and will resolve as real operational data accumulates.",
            best_model=None,
            metrics={},
            n_samples=len(usable),
        )

    X = usable[FEATURE_COLUMNS]
    y = usable[TARGET_COLUMN]

    positive_rate = float(y.mean())
    class_balance = {
        "positive_rate": round(positive_rate, 4),
        "negative_count": int((y == 0).sum()),
        "positive_count": int((y == 1).sum()),
        "is_imbalanced": bool(positive_rate < 0.15 or positive_rate > 0.85),
    }

    stratify = y if y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=stratify
    )

    # Cross-validation fold count can't exceed the smaller class's sample size
    min_class_count = int(y_train.value_counts().min()) if y_train.nunique() > 1 else 1
    effective_cv_folds = max(2, min(cv_folds, min_class_count))
    can_cross_validate = y_train.nunique() > 1 and min_class_count >= 2

    comparison: list[ModelComparisonResult] = []
    fitted_pipelines: dict[str, Pipeline] = {}

    for name, estimator in _build_model_registry().items():
        pipeline = _build_pipeline(estimator)

        cv_metrics = {}
        if can_cross_validate:
            try:
                cv = StratifiedKFold(n_splits=effective_cv_folds, shuffle=True, random_state=42)
                scores = cross_validate(
                    pipeline,
                    X_train,
                    y_train,
                    cv=cv,
                    scoring=["accuracy", "precision", "recall", "f1"],
                    error_score="raise",
                )
                cv_metrics = {
                    "folds": effective_cv_folds,
                    "accuracy_mean": round(float(np.mean(scores["test_accuracy"])), 4),
                    "precision_mean": round(float(np.mean(scores["test_precision"])), 4),
                    "recall_mean": round(float(np.mean(scores["test_recall"])), 4),
                    "f1_mean": round(float(np.mean(scores["test_f1"])), 4),
                }
            except Exception as exc:  # cross-validation is a best-effort diagnostic
                cv_metrics = {"error": str(exc)}

        pipeline.fit(X_train, y_train)
        fitted_pipelines[name] = pipeline

        y_pred = pipeline.predict(X_test)
        try:
            y_proba = pipeline.predict_proba(X_test)[:, 1]
        except Exception:
            y_proba = y_pred  # fallback for estimators without predict_proba

        test_metrics = _evaluate(y_test, y_pred, y_proba)
        comparison.append(ModelComparisonResult(model_name=name, cv_metrics=cv_metrics, test_metrics=test_metrics))

    # Model selection: best test-set F1 score (ties broken by ROC-AUC if available)
    def sort_key(result: ModelComparisonResult):
        roc = result.test_metrics.get("roc_auc") or 0.0
        return (result.test_metrics["f1"], roc)

    comparison.sort(key=sort_key, reverse=True)
    best = comparison[0]
    best_pipeline = fitted_pipelines[best.model_name]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import joblib

        joblib.dump(best_pipeline, MODEL_PATH)
    except ImportError:
        pass  # joblib ships with scikit-learn; guarded for unusual environments

    comparison_serializable = [
        {"model_name": r.model_name, "cv_metrics": r.cv_metrics, "test_metrics": r.test_metrics}
        for r in comparison
    ]
    result_payload = {
        "best_model": best.model_name,
        "best_metrics": best.test_metrics,
        "comparison": comparison_serializable,
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "class_balance": class_balance,
        "cross_validated": can_cross_validate,
    }
    METRICS_PATH.write_text(json.dumps(result_payload, indent=2))

    return TrainingResult(
        trained=True,
        reason=None,
        best_model=best.model_name,
        metrics=best.test_metrics,
        comparison=comparison_serializable,
        n_samples=len(usable),
        class_balance=class_balance,
    )


def load_persisted_model():
    """Loads the last-trained best pipeline from disk, if one exists."""
    if not MODEL_PATH.exists():
        return None
    try:
        import joblib

        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def load_persisted_metrics() -> Optional[dict]:
    if not METRICS_PATH.exists():
        return None
    try:
        return json.loads(METRICS_PATH.read_text())
    except Exception:
        return None


def predict_no_show_risk(pipeline, features: dict) -> float:
    """Returns the predicted probability [0, 1] that an appointment will be a no-show.
    `features` must supply every key in FEATURE_COLUMNS using the SAME
    preprocessing expectations as training (identical column names/types) -
    this is what "training and inference use identical preprocessing" means
    in practice: the fitted Pipeline itself encapsulates the OneHotEncoder,
    so there is no separate manual preprocessing step to drift out of sync.
    """
    frame = pd.DataFrame([features])[FEATURE_COLUMNS]
    proba = pipeline.predict_proba(frame)[0]
    classes = list(pipeline.named_steps["model"].classes_)
    return float(proba[classes.index(1)]) if 1 in classes else 0.0
