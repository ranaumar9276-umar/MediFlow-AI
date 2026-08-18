from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus
from app.schemas.doctor import DoctorCreate, DoctorUpdate


def _ensure_department_exists(db: Session, department_id: int) -> None:
    if not db.query(Department).filter(Department.id == department_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")


def list_doctors(
    db: Session, department_id: Optional[int] = None, skip: int = 0, limit: int = 50
) -> tuple[list[Doctor], int]:
    query = db.query(Doctor)
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    total = query.count()
    doctors = query.order_by(Doctor.id.desc()).offset(skip).limit(limit).all()
    return doctors, total


def get_doctor(db: Session, doctor_id: int) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor


def create_doctor(db: Session, payload: DoctorCreate) -> Doctor:
    _ensure_department_exists(db, payload.department_id)
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def update_doctor(db: Session, doctor_id: int, payload: DoctorUpdate) -> Doctor:
    doctor = get_doctor(db, doctor_id)
    data = payload.model_dump(exclude_unset=True)
    if "department_id" in data:
        _ensure_department_exists(db, data["department_id"])
    for field, value in data.items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor


def delete_doctor(db: Session, doctor_id: int) -> None:
    doctor = get_doctor(db, doctor_id)
    active_appts = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id, Appointment.status == AppointmentStatus.SCHEDULED)
        .count()
    )
    if active_appts > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a doctor with scheduled appointments. Reassign or cancel them first.",
        )
    db.delete(doctor)
    db.commit()


def active_appointment_count(db: Session, doctor_id: int) -> int:
    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id, Appointment.status == AppointmentStatus.SCHEDULED)
        .count()
    )
