from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import AppointmentStatus


class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    reason: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentOut(AppointmentBase):
    id: int
    status: AppointmentStatus
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    wait_time_minutes: Optional[float] = None

    model_config = {"from_attributes": True}
