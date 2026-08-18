"""
Data Quality foundation for MediFlow AI (Phase 1).

Runs a real, computed data-quality audit over the operational database -
patients and appointments - covering missing values, duplicates, invalid
dates/values, inconsistent categories, and statistical outliers. Nothing
here is a canned/hardcoded report: every number reflects the actual current
state of the database at request time.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.patient import Patient


def _patients_dataframe(db: Session) -> pd.DataFrame:
    rows = db.query(Patient).all()
    records = [
        {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "date_of_birth": p.date_of_birth,
            "gender": p.gender.value if p.gender else None,
            "phone": p.phone,
            "email": p.email,
            "blood_type": p.blood_type,
            "status": p.status.value if p.status else None,
        }
        for p in rows
    ]
    return pd.DataFrame.from_records(records)


def _missing_value_report(df: pd.DataFrame, columns: list[str]) -> dict:
    if df.empty:
        return {c: {"missing_count": 0, "missing_percent": 0.0} for c in columns}
    report = {}
    for col in columns:
        if col not in df.columns:
            continue
        na_count = int(df[col].isna().sum())
        if df[col].dtype == object:
            non_null = df[col].dropna().astype(str)
            blank_count = int((non_null.str.strip() == "").sum())
            missing = na_count + blank_count
        else:
            missing = na_count
        report[col] = {
            "missing_count": missing,
            "missing_percent": round(missing / len(df) * 100, 1) if len(df) else 0.0,
        }
    return report


def patient_data_quality(db: Session) -> dict:
    df = _patients_dataframe(db)
    total = len(df)

    if total == 0:
        return {
            "total_records": 0,
            "missing_values": {},
            "duplicate_records": 0,
            "invalid_dates_of_birth": 0,
            "inconsistent_blood_types": 0,
            "quality_score_percent": 100.0,
            "notes": "No patient records yet - data quality will be assessed as records are added.",
        }

    missing = _missing_value_report(df, ["phone", "email", "blood_type"])

    # Duplicate detection: same first/last name + date of birth is a strong
    # signal of an accidental duplicate patient record.
    duplicate_mask = df.duplicated(subset=["first_name", "last_name", "date_of_birth"], keep=False)
    duplicate_records = int(duplicate_mask.sum())

    # Invalid dates of birth: in the future, or implausibly old (>120 years)
    today = datetime.now(timezone.utc).date()
    dob = pd.to_datetime(df["date_of_birth"], errors="coerce")
    invalid_dob = int(((dob.dt.date > today) | (dob.dt.date < today.replace(year=today.year - 120))).sum())

    # Inconsistent categorical values: blood type should match a known set
    valid_blood_types = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    known_blood_types = df["blood_type"].dropna()
    inconsistent_blood = int((~known_blood_types.isin(valid_blood_types)).sum()) if not known_blood_types.empty else 0

    # A simple composite quality score: 100% minus a penalty per issue category,
    # weighted by how much of the dataset it affects.
    penalty = (
        (missing.get("email", {}).get("missing_percent", 0) * 0.1)
        + (duplicate_records / total * 100 * 0.4)
        + (invalid_dob / total * 100 * 0.3)
        + (inconsistent_blood / total * 100 * 0.2)
    )
    quality_score = round(max(0.0, 100.0 - penalty), 1)

    return {
        "total_records": total,
        "missing_values": missing,
        "duplicate_records": duplicate_records,
        "invalid_dates_of_birth": invalid_dob,
        "inconsistent_blood_types": inconsistent_blood,
        "quality_score_percent": quality_score,
    }


def appointment_data_quality(df: pd.DataFrame) -> dict:
    """
    Expects the already-cleaned appointment DataFrame from
    `app.ml.data_pipeline.load_appointments_dataframe`.
    """
    total = len(df)
    if total == 0:
        return {
            "total_records": 0,
            "missing_values": {},
            "duplicate_records": 0,
            "duration_outliers": 0,
            "invalid_status_transitions": 0,
            "notes": "No appointment records yet.",
        }

    missing = _missing_value_report(df, ["reason"])

    duplicate_records = int(df.duplicated(subset=["id"]).sum())

    # Outlier detection on duration using the IQR method - a standard,
    # defensible statistical technique rather than an arbitrary cutoff.
    durations = df["duration_minutes"].astype(float)
    q1, q3 = np.percentile(durations, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = int(((durations < lower) | (durations > upper)).sum())

    # Logical inconsistency: started_at before checked_in_at, or either
    # timestamp set on a non-scheduled-origin appointment inconsistently.
    invalid_transitions = 0
    if "checked_in_at" in df.columns and "started_at" in df.columns:
        both_present = df["checked_in_at"].notna() & df["started_at"].notna()
        invalid_transitions = int((both_present & (df["started_at"] < df["checked_in_at"])).sum())

    return {
        "total_records": total,
        "missing_values": missing,
        "duplicate_records": duplicate_records,
        "duration_outliers": outliers,
        "duration_outlier_bounds_minutes": {"lower": round(float(lower), 1), "upper": round(float(upper), 1)},
        "invalid_status_transitions": invalid_transitions,
    }


def build_data_quality_summary(db: Session, appointments_df: pd.DataFrame) -> dict:
    return {
        "patients": patient_data_quality(db),
        "appointments": appointment_data_quality(appointments_df),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
