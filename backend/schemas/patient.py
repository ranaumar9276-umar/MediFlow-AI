from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Gender, PatientStatus


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender = Gender.UNSPECIFIED
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    blood_type: Optional[str] = Field(default=None, max_length=5)
    status: PatientStatus = PatientStatus.ACTIVE
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    status: Optional[PatientStatus] = None
    notes: Optional[str] = None


class PatientOut(PatientBase):
    id: int
    full_name: str
    appointment_count: int = 0

    model_config = {"from_attributes": True}
