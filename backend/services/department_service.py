from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.doctor import Doctor
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def list_departments(db: Session) -> list[Department]:
    return db.query(Department).order_by(Department.name.asc()).all()


def get_department(db: Session, department_id: int) -> Department:
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    if db.query(Department).filter(Department.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name already exists")
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def update_department(db: Session, department_id: int, payload: DepartmentUpdate) -> Department:
    department = get_department(db, department_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    db.commit()
    db.refresh(department)
    return department


def delete_department(db: Session, department_id: int) -> None:
    department = get_department(db, department_id)
    doctor_count = db.query(Doctor).filter(Doctor.department_id == department_id).count()
    if doctor_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a department with assigned doctors.",
        )
    db.delete(department)
    db.commit()
