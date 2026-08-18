from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["Departments"])


def _to_out(d) -> DepartmentOut:
    stats = {"doctor_count": len(d.doctors), "appointment_count": len(d.appointments)}
    return DepartmentOut.model_validate(
        {**{c.name: getattr(d, c.name) for c in d.__table__.columns}, **stats}
    )


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [_to_out(d) for d in department_service.list_departments(db)]


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return _to_out(department_service.get_department(db, department_id))


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    return _to_out(department_service.create_department(db, payload))


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOSPITAL_MANAGER)),
):
    return _to_out(department_service.update_department(db, department_id, payload))


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.ADMIN)),
):
    department_service.delete_department(db, department_id)
