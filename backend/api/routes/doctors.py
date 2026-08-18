from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorOut, DoctorUpdate
from app.services import doctor_service

router = APIRouter(prefix="/doctors", tags=["Doctors"])


def _to_out(d) -> DoctorOut:
    return DoctorOut.model_validate(
        {
            **{c.name: getattr(d, c.name) for c in d.__table__.columns},
            "department_name": d.department.name if d.department else None,
            "active_appointment_count": sum(1 for a in d.appointments if a.status.value == "SCHEDULED"),
        }
    )


@router.get("", response_model=dict)
def list_doctors(
    department_id: Optional[int] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    doctors, total = doctor_service.list_doctors(db, department_id=department_id, skip=skip, limit=limit)
    return {"items": [_to_out(d) for d in doctors], "total": total, "skip": skip, "limit": limit}


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return _to_out(doctor_service.get_doctor(db, doctor_id))


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    return _to_out(doctor_service.create_doctor(db, payload))


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    return _to_out(doctor_service.update_doctor(db, doctor_id, payload))


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    doctor_service.delete_doctor(db, doctor_id)
