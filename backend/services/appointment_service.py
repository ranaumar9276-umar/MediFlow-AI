from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


def _check_doctor_conflict(
    db: Session,
    doctor_id: int,
    scheduled_at: datetime,
    duration_minutes: int,
    exclude_appointment_id: Optional[int] = None,
) -> None:
    """Prevent double-booking the same doctor for overlapping time windows."""
    new_start = scheduled_at
    new_end = scheduled_at + timedelta(minutes=duration_minutes)

    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status == AppointmentStatus.SCHEDULED,
    )
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)

    for existing in query.all():
        existing_start = existing.scheduled_at
        existing_end = existing.scheduled_at + timedelta(minutes=existing.duration_minutes)
        overlap = new_start < existing_end and existing_start < new_end
        if overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Doctor already has an appointment overlapping this time slot "
                f"({existing_start.isoformat()} - {existing_end.isoformat()}).",
            )


def list_appointments(
    db: Session,
    status_filter: Optional[AppointmentStatus] = None,
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    department_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Appointment], int]:
    query = db.query(Appointment)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if department_id:
        query = query.filter(Appointment.department_id == department_id)
    if date_from:
        query = query.filter(Appointment.scheduled_at >= date_from)
    if date_to:
        query = query.filter(Appointment.scheduled_at <= date_to)

    total = query.count()
    appointments = query.order_by(Appointment.scheduled_at.desc()).offset(skip).limit(limit).all()
    return appointments, total


def get_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment


def create_appointment(db: Session, payload: AppointmentCreate, created_by_id: Optional[int]) -> Appointment:
    if not db.query(Patient).filter(Patient.id == payload.patient_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient does not exist")
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor does not exist")
    if doctor.department_id != payload.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor does not belong to the specified department",
        )

    _check_doctor_conflict(db, payload.doctor_id, payload.scheduled_at, payload.duration_minutes)

    appointment = Appointment(**payload.model_dump(), created_by_id=created_by_id)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def update_appointment(db: Session, appointment_id: int, payload: AppointmentUpdate) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    data = payload.model_dump(exclude_unset=True)

    new_doctor_id = data.get("doctor_id", appointment.doctor_id)
    new_time = data.get("scheduled_at", appointment.scheduled_at)
    new_duration = data.get("duration_minutes", appointment.duration_minutes)

    if any(k in data for k in ("doctor_id", "scheduled_at", "duration_minutes")):
        _check_doctor_conflict(
            db, new_doctor_id, new_time, new_duration, exclude_appointment_id=appointment_id
        )

    for field, value in data.items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    if appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled appointments can be cancelled",
        )
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment


def mark_completed(db: Session, appointment_id: int) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    appointment.status = AppointmentStatus.COMPLETED
    db.commit()
    db.refresh(appointment)
    return appointment


def check_in_appointment(db: Session, appointment_id: int) -> Appointment:
    """
    Records the patient's arrival time. This is what enables real
    waiting-time analytics (Phase 1) - wait time = started_at - checked_in_at.
    """
    appointment = get_appointment(db, appointment_id)
    if appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled appointments can be checked in",
        )
    if appointment.checked_in_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment already checked in")
    appointment.checked_in_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(appointment)
    return appointment


def start_appointment(db: Session, appointment_id: int) -> Appointment:
    """Records when the doctor actually begins seeing the patient."""
    appointment = get_appointment(db, appointment_id)
    if appointment.status != AppointmentStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled appointments can be started",
        )
    if appointment.checked_in_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment must be checked in before it can be started",
        )
    if appointment.started_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment already started")
    appointment.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(appointment)
    return appointment


def mark_no_show(db: Session, appointment_id: int) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    appointment.status = AppointmentStatus.NO_SHOW
    db.commit()
    db.refresh(appointment)
    return appointment


def delete_appointment(db: Session, appointment_id: int) -> None:
    appointment = get_appointment(db, appointment_id)
    db.delete(appointment)
    db.commit()
