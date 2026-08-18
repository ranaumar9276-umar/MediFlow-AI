from typing import Optional

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = None
    location: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None
    location: Optional[str] = None


class DepartmentOut(DepartmentBase):
    id: int
    doctor_count: int = 0
    appointment_count: int = 0

    model_config = {"from_attributes": True}
