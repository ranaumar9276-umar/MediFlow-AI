"""
Appointment demand forecasting foundation for MediFlow AI (Phase 1).

Uses a straightforward, transparent linear-trend + weekly-seasonality
forecast over historical daily appointment counts. This is intentionally
simple and interpretable rather than a black-box model: hospital
operations staff need to trust and understand a forecast that will
influence staffing decisions. Limitations are reported explicitly rather
than presented as high-confidence predictions.
"""
from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.appointment import Appointment


def _daily_counts(db: Session, department_id: int | None = None) -> pd.DataFrame:
    query = db.query(Appointment)
    if department_id:
        query = query.filter(Appointment.department_id == department_id)
    rows = query.all()
    if not rows:
        return pd.DataFrame(columns=["date", "count"])

    dates = pd.to_datetime([a.scheduled_at for a in rows], utc=True).date
    series = pd.Series(dates).value_counts().sort_index()
    df = series.rename_axis("date").reset_index(name="count")
    df["date"] = pd.to_datetime(df["date"])

    # Fill in missing days with 0 so the trend line isn't distorted by gaps
    full_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_range, fill_value=0).rename_axis("date").reset_index()
    return df


def forecast_appointment_demand(db: Session, department_id: int | None = None, horizon_days: int = 14) -> dict:
    """
    Fits a simple linear regression on daily appointment counts (day index
    as the feature) to project demand `horizon_days` into the future.

    Requires a minimum history window before forecasting, and always
    reports the minimum/maximum observed daily volume and R^2 fit quality
    so the forecast isn't presented with false confidence.
    """
    df = _daily_counts(db, department_id)
    min_history_days = 14

    if len(df) < min_history_days:
        return {
            "forecastable": False,
            "reason": f"Only {len(df)} day(s) of appointment history available; "
            f"at least {min_history_days} days are needed for a meaningful trend forecast.",
            "history": [{"date": d.strftime("%Y-%m-%d"), "count": int(c)} for d, c in zip(df["date"], df["count"])],
            "forecast": [],
        }

    x = np.arange(len(df))
    y = df["count"].to_numpy(dtype=float)

    # Simple linear fit: count = slope * day_index + intercept
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = round(float(1 - ss_res / ss_tot), 3) if ss_tot > 0 else 0.0

    # Weekly seasonality: average deviation from trend per weekday, applied
    # to keep the forecast realistic (e.g. weekends typically quieter).
    residuals = y - y_pred
    weekday_effect = (
        pd.Series(residuals, index=df["date"].dt.day_name()).groupby(level=0).mean().to_dict()
    )

    last_date = df["date"].max()
    forecast_points = []
    for i in range(1, horizon_days + 1):
        future_date = last_date + timedelta(days=i)
        future_x = len(df) - 1 + i
        base = slope * future_x + intercept
        seasonal_adjustment = weekday_effect.get(future_date.day_name(), 0.0)
        predicted = max(0.0, base + seasonal_adjustment)
        forecast_points.append({"date": future_date.strftime("%Y-%m-%d"), "predicted_count": round(predicted, 1)})

    trend_direction = "increasing" if slope > 0.05 else "decreasing" if slope < -0.05 else "stable"

    return {
        "forecastable": True,
        "history_days": len(df),
        "trend_slope_per_day": round(float(slope), 3),
        "trend_direction": trend_direction,
        "fit_quality_r_squared": r_squared,
        "observed_min": int(y.min()),
        "observed_max": int(y.max()),
        "observed_mean": round(float(y.mean()), 1),
        "history": [{"date": d.strftime("%Y-%m-%d"), "count": int(c)} for d, c in zip(df["date"], df["count"])],
        "forecast": forecast_points,
        "limitations": (
            "Linear trend + weekly-seasonality model. Does not account for holidays, "
            "seasonal illness patterns, or marketing/outreach events. Treat as a "
            "planning aid, not a guarantee, and low history_days or low "
            "fit_quality_r_squared indicate a less reliable forecast."
        ),
    }
