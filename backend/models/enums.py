"""Shared enumerations used across ORM models and Pydantic schemas."""
import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    HOSPITAL_MANAGER = "HOSPITAL_MANAGER"
    DOCTOR = "DOCTOR"
    STAFF = "STAFF"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class PatientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCHARGED = "DISCHARGED"
    INACTIVE = "INACTIVE"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    UNSPECIFIED = "UNSPECIFIED"
