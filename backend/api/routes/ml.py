"""
ML routes for MediFlow AI (Phase 1) - integrated directly into the existing
FastAPI application (no separate backend/service). Exposes:

- POST /ml/train         - trains and compares candidate models, persists the best one
- GET  /ml/model-info     - returns metrics from the last training run
- POST /ml/predict-no-show - real-time no-show risk prediction for a candidate appointment

Training is restricted to ADMIN/HOSPITAL_MANAGER since it mutates a
persisted model artifact used by all subsequent predictions.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.user import User
from app.ml.data_pipeline import load_appointments_dataframe
from app.ml.noshow_model import (
    load_persisted_metrics,
    load_persisted_model,
    predict_no_show_risk,
    train_and_compare_models,
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/train")
def train_model(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    """
    Trains and compares Logistic Regression, Decision Tree, Random Forest
    (and XGBoost if installed) with cross-validation on real appointment
    history, selects the best model by test-set F1 score, and persists it.
    Returns the full comparison so the choice is auditable, not a black box.
    """
    df = load_appointments_dataframe(db)
    result = train_and_compare_models(df)

    if not result.trained:
        return {
            "trained": False,
            "reason": result.reason,
            "n_samples": result.n_samples,
        }

    return {
        "trained": True,
        "best_model": result.best_model,
        "metrics": result.metrics,
        "comparison": result.comparison,
        "n_samples": result.n_samples,
        "class_balance": result.class_balance,
        "trained_at": datetime.utcnow().isoformat(),
    }


@router.get("/model-info")
def model_info(_user: User = Depends(get_current_user)):
    """Returns metrics/comparison from the most recent training run, if any."""
    metrics = load_persisted_metrics()
    if metrics is None:
        return {"model_available": False, "message": "No model has been trained yet. Use POST /ml/train."}
    return {"model_available": True, **metrics}


class NoShowPredictionRequest(BaseModel):
    doctor_id: int
    department_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    patient_prior_appointment_count: int = Field(
        default=0, ge=0, description="How many prior appointments this patient has had"
    )
    patient_prior_no_show_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="This patient's historical no-show rate (0-1)"
    )


class NoShowPredictionResponse(BaseModel):
    no_show_risk_probability: float
    risk_level: str
    model_used: str


@router.post("/predict-no-show", response_model=NoShowPredictionResponse)
def predict_no_show(
    payload: NoShowPredictionRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Real-time no-show risk prediction using the persisted best model.
    Applies the EXACT SAME preprocessing pipeline used at training time
    (the fitted sklearn Pipeline bundles the OneHotEncoder + model
    together), eliminating train/inference preprocessing drift.
    """
    pipeline = load_persisted_model()
    metrics = load_persisted_metrics()
    if pipeline is None or metrics is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No trained model is available yet. An admin must run POST /ml/train first "
            "(requires sufficient labeled appointment history).",
        )

    department = db.query(Department).filter(Department.id == payload.department_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor does not exist")

    features = {
        "department": department.name,
        "weekday": payload.scheduled_at.strftime("%A"),
        "hour_of_day": payload.scheduled_at.hour,
        "duration_minutes": payload.duration_minutes,
        "patient_prior_appointment_count": payload.patient_prior_appointment_count,
        "patient_prior_no_show_rate": payload.patient_prior_no_show_rate,
    }

    try:
        risk = predict_no_show_risk(pipeline, features)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )

    if risk >= 0.6:
        level = "HIGH"
    elif risk >= 0.3:
        level = "MEDIUM"
    else:
        level = "LOW"

    return NoShowPredictionResponse(
        no_show_risk_probability=round(risk, 4),
        risk_level=level,
        model_used=metrics.get("best_model", "unknown"),
    )
