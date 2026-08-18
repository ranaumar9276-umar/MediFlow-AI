"""
Data Science foundation for MediFlow AI.

Responsibilities (Phase 0 scope):
- Load appointment records from PostgreSQL into a pandas DataFrame
- Clean/normalize the data (missing values, dtype correction, duplicates)
- Provide descriptive statistics and simple exploratory summaries used by
  the /analytics endpoints and, later, by the Phase 1 ML pipeline.

This module intentionally has NO FastAPI/HTTP concerns - it is pure
Python/Pandas/NumPy so it can be reused by the API layer, batch scripts,
notebooks, or the ML training pipeline in `app/ml/noshow_model.py`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.appointment import Appointment


def load_appointments_dataframe(db: Session) -> pd.DataFrame:
    """Pull all appointments from the database into a cleaned DataFrame."""
    rows = db.query(Appointment).all()

    records = [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.full_name if a.doctor else None,
            "department_id": a.department_id,
            "department": a.department.name if a.department else None,
            "scheduled_at": a.scheduled_at,
            "duration_minutes": a.duration_minutes,
            "status": a.status.value,
            "reason": a.reason,
            "checked_in_at": a.checked_in_at,
            "started_at": a.started_at,
        }
        for a in rows
    ]

    df = pd.DataFrame.from_records(records)
    return clean_appointments_dataframe(df)


def clean_appointments_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standard data-cleaning pass:
    - Ensures expected columns exist even for an empty dataset
    - Drops exact duplicate rows
    - Coerces dtypes (datetime, category)
    - Fills missing categorical values with an explicit "Unknown" label
      (never silently drops rows with missing non-critical fields)
    """
    expected_columns = [
        "id", "patient_id", "doctor_id", "doctor_name", "department_id", "department",
        "scheduled_at", "duration_minutes", "status", "reason",
        "checked_in_at", "started_at",
    ]
    if df.empty:
        return pd.DataFrame(columns=expected_columns)

    df = df.drop_duplicates(subset=["id"]).copy()
    df["scheduled_at"] = pd.to_datetime(df["scheduled_at"], utc=True, errors="coerce")
    df["checked_in_at"] = pd.to_datetime(df["checked_in_at"], utc=True, errors="coerce")
    df["started_at"] = pd.to_datetime(df["started_at"], utc=True, errors="coerce")
    df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce").fillna(30).astype(int)
    df["department"] = df["department"].fillna("Unknown")
    df["doctor_name"] = df["doctor_name"].fillna("Unknown")
    df["reason"] = df["reason"].fillna("Not specified")
    df["status"] = df["status"].astype("category")
    df["weekday"] = df["scheduled_at"].dt.day_name()
    df["hour_of_day"] = df["scheduled_at"].dt.hour

    # Wait time in minutes - only defined where both timestamps are present
    wait = (df["started_at"] - df["checked_in_at"]).dt.total_seconds() / 60
    df["wait_time_minutes"] = wait.where(wait.notna() & (wait >= 0))

    return df


def appointment_statistics(df: pd.DataFrame) -> dict:
    """Descriptive statistics (mean/median/std/percentiles) over durations,
    plus status breakdown counts - a practical use of basic statistics on
    real hospital operational data."""
    if df.empty:
        return {
            "duration_minutes": {"mean": 0, "median": 0, "std": 0, "p25": 0, "p75": 0, "p90": 0},
            "status_breakdown": {},
        }

    durations = df["duration_minutes"].astype(float)
    stats = {
        "duration_minutes": {
            "mean": round(float(np.mean(durations)), 2),
            "median": round(float(np.median(durations)), 2),
            "std": round(float(np.std(durations)), 2),
            "p25": round(float(np.percentile(durations, 25)), 2),
            "p75": round(float(np.percentile(durations, 75)), 2),
            "p90": round(float(np.percentile(durations, 90)), 2),
        },
        "status_breakdown": df["status"].value_counts().to_dict(),
    }
    return stats


def weekday_distribution(df: pd.DataFrame) -> dict:
    """Count of appointments per weekday - used for patient-flow analysis."""
    if df.empty or "weekday" not in df.columns:
        return {}
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = df["weekday"].value_counts().reindex(order).fillna(0).astype(int)
    return counts.to_dict()


def waiting_time_analysis(df: pd.DataFrame) -> dict:
    """
    Real waiting-time analytics computed from checked_in_at/started_at
    timestamps (Phase 1). Returns an explicit "insufficient data" signal
    rather than fabricating numbers when no check-in/start events have been
    recorded yet - this is expected for a freshly-deployed hospital.
    """
    if df.empty or "wait_time_minutes" not in df.columns:
        return {"sample_size": 0, "has_data": False}

    waits = df["wait_time_minutes"].dropna()
    if waits.empty:
        return {"sample_size": 0, "has_data": False}

    by_department = (
        df.dropna(subset=["wait_time_minutes"]).groupby("department")["wait_time_minutes"].mean().round(1).to_dict()
    )
    by_doctor = (
        df.dropna(subset=["wait_time_minutes"]).groupby("doctor_name")["wait_time_minutes"].mean().round(1).to_dict()
    )

    return {
        "sample_size": int(len(waits)),
        "has_data": True,
        "mean_minutes": round(float(np.mean(waits)), 1),
        "median_minutes": round(float(np.median(waits)), 1),
        "p90_minutes": round(float(np.percentile(waits, 90)), 1),
        "max_minutes": round(float(np.max(waits)), 1),
        "by_department": by_department,
        "by_doctor": by_doctor,
    }


def peak_period_analysis(df: pd.DataFrame) -> dict:
    """Identifies the busiest weekday and hour-of-day windows from real
    scheduled-appointment volume - used to flag capacity/staffing risk."""
    if df.empty:
        return {"peak_weekday": None, "peak_hour": None, "hourly_distribution": {}}

    hourly = df["hour_of_day"].value_counts().sort_index()
    weekday_counts = df["weekday"].value_counts()

    return {
        "peak_weekday": weekday_counts.idxmax() if not weekday_counts.empty else None,
        "peak_weekday_count": int(weekday_counts.max()) if not weekday_counts.empty else 0,
        "peak_hour": int(hourly.idxmax()) if not hourly.empty else None,
        "peak_hour_count": int(hourly.max()) if not hourly.empty else 0,
        "hourly_distribution": {int(h): int(c) for h, c in hourly.items()},
    }


def cancellation_no_show_analysis(df: pd.DataFrame) -> dict:
    """Cancellation and no-show breakdowns by department and doctor,
    computed from real status data (not the simple rate already shown on
    the Phase 0 dashboard - this drills into *where* the problem is)."""
    if df.empty:
        return {"by_department": {}, "by_doctor": {}}

    def rate_table(group_col: str) -> dict:
        result = {}
        for key, group in df.groupby(group_col, observed=True):
            total = len(group)
            if total == 0:
                continue
            cancelled = int((group["status"] == "CANCELLED").sum())
            no_show = int((group["status"] == "NO_SHOW").sum())
            result[str(key)] = {
                "total": total,
                "cancelled": cancelled,
                "no_show": no_show,
                "cancellation_rate_percent": round(cancelled / total * 100, 1),
                "no_show_rate_percent": round(no_show / total * 100, 1),
            }
        return result

    return {
        "by_department": rate_table("department"),
        "by_doctor": rate_table("doctor_name"),
    }
