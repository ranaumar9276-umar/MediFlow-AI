from pydantic import BaseModel


class DepartmentWorkload(BaseModel):
    department: str
    total_appointments: int
    completed: int
    cancelled: int
    no_show: int


class DoctorWorkload(BaseModel):
    doctor: str
    department: str
    total_appointments: int
    completed: int
    upcoming: int


class TrendPoint(BaseModel):
    label: str
    value: int


class DashboardSummary(BaseModel):
    total_patients: int
    total_doctors: int
    total_departments: int
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_show_appointments: int
    scheduled_appointments: int
    no_show_rate_percent: float
    cancellation_rate_percent: float
    department_workload: list[DepartmentWorkload]
    doctor_workload: list[DoctorWorkload]
    appointment_trend_last_14_days: list[TrendPoint]
