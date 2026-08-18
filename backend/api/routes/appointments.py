from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import AppointmentStatus, UserRole
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _to_out(a) -> AppointmentOut:
    wait_time_minutes = None
    if a.checked_in_at and a.started_at:
        wait_time_minutes = round((a.started_at - a.checked_in_at).total_seconds() / 60, 1)

    return AppointmentOut.model_validate(
        {
            **{c.name: getattr(a, c.name) for c in a.__table__.columns},
            "patient_name": a.patient.full_name if a.patient else None,
            "doctor_name": a.doctor.full_name if a.doctor else None,
            "department_name": a.department.name if a.department else None,
            "wait_time_minutes": wait_time_minutes,
        }
    )


@router.get("", response_model=dict)
def list_appointments(
    status_filter: Optional[AppointmentStatus] = Query(default=None, alias="status"),
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    department_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    appointments, total = appointment_service.list_appointments(
        db,
        status_filter=status_filter,
        doctor_id=doctor_id,
        patient_id=patient_id,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return {"items": [_to_out(a) for a in appointments], "total": total, "skip": skip, "limit": limit}


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return _to_out(appointment_service.get_appointment(db, appointment_id))


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF, UserRole.DOCTOR)),
):
    appointment = appointment_service.create_appointment(db, payload, created_by_id=current_user.id)
    return _to_out(appointment)


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF, UserRole.DOCTOR)),
):
    return _to_out(appointment_service.update_appointment(db, appointment_id, payload))


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF, UserRole.DOCTOR)),
):
    return _to_out(appointment_service.cancel_appointment(db, appointment_id))


@router.post("/{appointment_id}/complete", response_model=AppointmentOut)
def complete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.DOCTOR)),
):
    return _to_out(appointment_service.mark_completed(db, appointment_id))


@router.post("/{appointment_id}/check-in", response_model=AppointmentOut)
def check_in_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF, UserRole.DOCTOR)),
):
    """Records patient arrival time - feeds Phase 1 waiting-time analytics."""
    return _to_out(appointment_service.check_in_appointment(db, appointment_id))


@router.post("/{appointment_id}/start", response_model=AppointmentOut)
def start_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.DOCTOR)),
):
    """Records when the doctor actually begins the consultation."""
    return _to_out(appointment_service.start_appointment(db, appointment_id))


@router.post("/{appointment_id}/no-show", response_model=AppointmentOut)
def no_show_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF, UserRole.DOCTOR)),
):
    return _to_out(appointment_service.mark_no_show(db, appointment_id))


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN)),
):
    appointment_service.delete_appointment(db, appointment_id)
