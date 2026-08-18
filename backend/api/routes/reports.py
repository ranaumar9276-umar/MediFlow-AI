"""
Reporting endpoints for MediFlow AI (Phase 1).

Reuses the existing appointment_service query logic (same filters as the
Appointments list) but returns a report-shaped payload: the filtered rows
plus aggregate summary statistics, all computed live - no separate/fake
reporting datastore.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import AppointmentStatus
from app.models.user import User
from app.services import appointment_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/appointments")
def appointment_report(
    status_filter: Optional[AppointmentStatus] = Query(default=None, alias="status"),
    doctor_id: Optional[int] = None,
    department_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Filterable appointment report. Supports the same filters as the
    Appointments page (status, doctor, department, date range) plus a
    computed summary block (counts by status, average duration) over the
    filtered result set - all from real database queries.
    """
    appointments, total = appointment_service.list_appointments(
        db,
        status_filter=status_filter,
        doctor_id=doctor_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        skip=0,
        limit=1000,
    )

    status_counts: dict[str, int] = {}
    total_duration = 0
    for a in appointments:
        status_counts[a.status.value] = status_counts.get(a.status.value, 0) + 1
        total_duration += a.duration_minutes

    summary = {
        "total_appointments": total,
        "returned_rows": len(appointments),
        "status_counts": status_counts,
        "average_duration_minutes": round(total_duration / len(appointments), 1) if appointments else 0,
    }

    rows = [
        {
            "id": a.id,
            "patient_name": a.patient.full_name if a.patient else None,
            "doctor_name": a.doctor.full_name if a.doctor else None,
            "department_name": a.department.name if a.department else None,
            "scheduled_at": a.scheduled_at.isoformat(),
            "duration_minutes": a.duration_minutes,
            "status": a.status.value,
            "reason": a.reason,
        }
        for a in appointments
    ]

    return {"summary": summary, "rows": rows}
