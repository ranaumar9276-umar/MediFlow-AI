"""
Operational alerts for MediFlow AI (Phase 1).

Every alert here is derived from an actual calculation against live data -
no randomness, no placeholders. Thresholds are declared as named constants
so they are easy to review/tune, and each alert explains exactly which
number triggered it.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd
from sqlalchemy.orm import Session

from app.ml.data_pipeline import waiting_time_analysis
from app.ml.data_quality import build_data_quality_summary
from app.services.dashboard_service import build_dashboard_summary

# --- Thresholds (tune here; used consistently by all alert checks below) ---
HIGH_NO_SHOW_RATE_PERCENT = 15.0
HIGH_CANCELLATION_RATE_PERCENT = 20.0
HIGH_WAIT_TIME_MINUTES = 30.0
HIGH_DOCTOR_WORKLOAD_APPOINTMENTS = 40
LOW_DATA_QUALITY_SCORE_PERCENT = 85.0


@dataclass
class Alert:
    severity: str  # "critical" | "warning" | "info"
    category: str
    message: str
    metric_value: float


def build_operational_alerts(db: Session, appointments_df: pd.DataFrame) -> list[dict]:
    alerts: list[Alert] = []

    summary = build_dashboard_summary(db)

    if summary.no_show_rate_percent >= HIGH_NO_SHOW_RATE_PERCENT:
        alerts.append(
            Alert(
                severity="critical" if summary.no_show_rate_percent >= HIGH_NO_SHOW_RATE_PERCENT * 1.5 else "warning",
                category="no_show",
                message=f"Hospital-wide no-show rate is {summary.no_show_rate_percent}%, "
                f"above the {HIGH_NO_SHOW_RATE_PERCENT}% threshold.",
                metric_value=summary.no_show_rate_percent,
            )
        )

    if summary.cancellation_rate_percent >= HIGH_CANCELLATION_RATE_PERCENT:
        alerts.append(
            Alert(
                severity="warning",
                category="cancellation",
                message=f"Hospital-wide cancellation rate is {summary.cancellation_rate_percent}%, "
                f"above the {HIGH_CANCELLATION_RATE_PERCENT}% threshold.",
                metric_value=summary.cancellation_rate_percent,
            )
        )

    for dept in summary.department_workload:
        if dept.total_appointments == 0:
            continue
        dept_no_show_rate = round(dept.no_show / dept.total_appointments * 100, 1)
        if dept_no_show_rate >= HIGH_NO_SHOW_RATE_PERCENT and dept.total_appointments >= 5:
            alerts.append(
                Alert(
                    severity="warning",
                    category="department_no_show",
                    message=f"{dept.department} has a {dept_no_show_rate}% no-show rate "
                    f"({dept.no_show}/{dept.total_appointments} appointments).",
                    metric_value=dept_no_show_rate,
                )
            )

    for doc in summary.doctor_workload:
        if doc.total_appointments >= HIGH_DOCTOR_WORKLOAD_APPOINTMENTS:
            alerts.append(
                Alert(
                    severity="info",
                    category="doctor_workload",
                    message=f"Dr. {doc.doctor} has a high total workload "
                    f"({doc.total_appointments} appointments recorded).",
                    metric_value=float(doc.total_appointments),
                )
            )

    wait_analysis = waiting_time_analysis(appointments_df)
    if wait_analysis.get("has_data") and wait_analysis["mean_minutes"] >= HIGH_WAIT_TIME_MINUTES:
        alerts.append(
            Alert(
                severity="warning",
                category="waiting_time",
                message=f"Average patient waiting time is {wait_analysis['mean_minutes']} minutes, "
                f"above the {HIGH_WAIT_TIME_MINUTES}-minute threshold.",
                metric_value=wait_analysis["mean_minutes"],
            )
        )

    dq = build_data_quality_summary(db, appointments_df)
    patient_score = dq["patients"].get("quality_score_percent")
    if patient_score is not None and patient_score < LOW_DATA_QUALITY_SCORE_PERCENT and dq["patients"]["total_records"] > 0:
        alerts.append(
            Alert(
                severity="info",
                category="data_quality",
                message=f"Patient record data-quality score is {patient_score}%, "
                f"below the {LOW_DATA_QUALITY_SCORE_PERCENT}% target (check duplicates/missing fields).",
                metric_value=patient_score,
            )
        )

    # Sort most severe first for a sensible default display order
    severity_rank = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_rank.get(a.severity, 3))

    return [asdict(a) for a in alerts]
