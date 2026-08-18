from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class DoctorBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    specialty: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = None
    department_id: int
    daily_capacity: int = Field(default=12, ge=1, le=100)
    is_active: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    specialty: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    daily_capacity: Optional[int] = Field(default=None, ge=1, le=100)
    is_active: Optional[bool] = None


class DoctorOut(DoctorBase):
    id: int
    department_name: Optional[str] = None
    active_appointment_count: int = 0

    model_config = {"from_attributes": True}
