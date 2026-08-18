from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


def list_patients(
    db: Session, search: Optional[str] = None, skip: int = 0, limit: int = 50
) -> tuple[list[Patient], int]:
    query = db.query(Patient)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Patient.first_name).like(like),
                func.lower(Patient.last_name).like(like),
                func.lower(Patient.email).like(like),
                Patient.phone.like(f"%{search}%"),
            )
        )
    total = query.count()
    patients = query.order_by(Patient.id.desc()).offset(skip).limit(limit).all()
    return patients, total


def get_patient(db: Session, patient_id: int) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient_id: int, payload: PatientUpdate) -> Patient:
    patient = get_patient(db, patient_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: int) -> None:
    patient = get_patient(db, patient_id)
    appointment_count = db.query(Appointment).filter(Appointment.patient_id == patient_id).count()
    if appointment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a patient with existing appointment history. "
            "Set status to INACTIVE instead.",
        )
    db.delete(patient)
    db.commit()
