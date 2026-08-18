"""
Analytics foundation endpoints.

These use pandas/numpy directly on data pulled from PostgreSQL to compute
descriptive statistics (mean, std, percentiles, weekday distribution, etc.)
that go beyond the simple counters in /dashboard/summary. Phase 0 provided
the descriptive-statistics foundation; Phase 1 extends this with
waiting-time analysis, peak-period analysis, cancellation/no-show
drill-downs, data-quality auditing, matplotlib/seaborn EDA charts, demand
forecasting, and operational alerts - all still computed live, never
hardcoded.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.ml.data_pipeline import (
    appointment_statistics,
    cancellation_no_show_analysis,
    load_appointments_dataframe,
    peak_period_analysis,
    waiting_time_analysis,
    weekday_distribution,
)
from app.ml.data_quality import build_data_quality_summary
from app.ml.eda import build_eda_charts
from app.ml.forecasting import forecast_appointment_demand
from app.services.alerts_service import build_operational_alerts

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/appointment-statistics")
def appointment_statistics_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    Real descriptive statistics (count, mean duration, std, percentiles,
    weekday distribution, status breakdown) computed with pandas/numpy from
    live appointment data - not hardcoded.
    """
    df = load_appointments_dataframe(db)
    return {
        "row_count": int(len(df)),
        "statistics": appointment_statistics(df),
        "weekday_distribution": weekday_distribution(df),
    }


@router.get("/waiting-time")
def waiting_time_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    Real waiting-time analytics (mean/median/p90, by department, by doctor)
    computed from checked_in_at/started_at timestamps recorded via the
    appointment check-in/start actions (Phase 1).
    """
    df = load_appointments_dataframe(db)
    return waiting_time_analysis(df)


@router.get("/peak-periods")
def peak_periods_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Busiest weekday/hour windows computed from real scheduled volume."""
    df = load_appointments_dataframe(db)
    return peak_period_analysis(df)


@router.get("/cancellation-no-show")
def cancellation_no_show_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Cancellation/no-show rate drill-down by department and by doctor."""
    df = load_appointments_dataframe(db)
    return cancellation_no_show_analysis(df)


@router.get("/data-quality")
def data_quality_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    Real data-quality audit: missing values, duplicate records, invalid
    dates, inconsistent categorical values, and statistical outliers -
    computed live over patients and appointments.
    """
    df = load_appointments_dataframe(db)
    return build_data_quality_summary(db, df)


@router.get("/eda-charts")
def eda_charts_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    Matplotlib/Seaborn-generated exploratory data analysis charts
    (duration distribution, weekday x hour heatmap, department/status
    breakdown) returned as base64-encoded PNGs for the frontend to render.
    """
    df = load_appointments_dataframe(db)
    return build_eda_charts(df)


@router.get("/forecast")
def forecast_endpoint(
    department_id: Optional[int] = Query(default=None),
    horizon_days: int = Query(default=14, ge=1, le=60),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Appointment demand forecast (overall or per-department) using a
    transparent linear-trend + weekly-seasonality model. Reports fit
    quality and explicit limitations rather than false confidence.
    """
    return forecast_appointment_demand(db, department_id=department_id, horizon_days=horizon_days)


@router.get("/alerts")
def alerts_endpoint(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    Operational alerts computed from real thresholds against live data
    (no-show rate, cancellation rate, waiting time, doctor workload, data
    quality). See app/services/alerts_service.py for threshold definitions.
    """
    df = load_appointments_dataframe(db)
    return {"alerts": build_operational_alerts(db, df)}
