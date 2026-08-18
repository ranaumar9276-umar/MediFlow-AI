from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientOut, PatientUpdate
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


def _to_out(p) -> PatientOut:
    return PatientOut.model_validate(
        {
            **{c.name: getattr(p, c.name) for c in p.__table__.columns},
            "full_name": p.full_name,
            "appointment_count": len(p.appointments),
        }
    )


@router.get("", response_model=dict)
def list_patients(
    search: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    patients, total = patient_service.list_patients(db, search=search, skip=skip, limit=limit)
    return {
        "items": [_to_out(p) for p in patients],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    patient = patient_service.get_patient(db, patient_id)
    return _to_out(patient)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF)),
):
    patient = patient_service.create_patient(db, payload)
    return _to_out(patient)


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER, UserRole.STAFF)),
):
    patient = patient_service.update_patient(db, patient_id, payload)
    return _to_out(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    patient_service.delete_patient(db, patient_id)
