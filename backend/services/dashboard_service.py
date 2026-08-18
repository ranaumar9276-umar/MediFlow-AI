from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus
from app.models.patient import Patient
from app.schemas.dashboard import DashboardSummary, DepartmentWorkload, DoctorWorkload, TrendPoint


def build_dashboard_summary(db: Session) -> DashboardSummary:
    total_patients = db.query(Patient).count()
    total_doctors = db.query(Doctor).count()
    total_departments = db.query(Department).count()
    total_appointments = db.query(Appointment).count()

    def count_status(s: AppointmentStatus) -> int:
        return db.query(Appointment).filter(Appointment.status == s).count()

    completed = count_status(AppointmentStatus.COMPLETED)
    cancelled = count_status(AppointmentStatus.CANCELLED)
    no_show = count_status(AppointmentStatus.NO_SHOW)
    scheduled = count_status(AppointmentStatus.SCHEDULED)

    resolved = completed + cancelled + no_show
    no_show_rate = round((no_show / resolved) * 100, 2) if resolved else 0.0
    cancellation_rate = round((cancelled / resolved) * 100, 2) if resolved else 0.0

    # --- Department workload ---
    # A simple per-department query set is used here (rather than one large
    # aggregate join) for clarity and portability across SQLite/PostgreSQL.
    department_workload: list[DepartmentWorkload] = []
    for dept in db.query(Department).order_by(Department.name.asc()).all():
        appts = db.query(Appointment).filter(Appointment.department_id == dept.id)
        department_workload.append(
            DepartmentWorkload(
                department=dept.name,
                total_appointments=appts.count(),
                completed=appts.filter(Appointment.status == AppointmentStatus.COMPLETED).count(),
                cancelled=appts.filter(Appointment.status == AppointmentStatus.CANCELLED).count(),
                no_show=appts.filter(Appointment.status == AppointmentStatus.NO_SHOW).count(),
            )
        )

    # --- Doctor workload ---
    doctor_workload: list[DoctorWorkload] = []
    for doc in db.query(Doctor).order_by(Doctor.full_name.asc()).all():
        appts = db.query(Appointment).filter(Appointment.doctor_id == doc.id)
        doctor_workload.append(
            DoctorWorkload(
                doctor=doc.full_name,
                department=doc.department.name if doc.department else "",
                total_appointments=appts.count(),
                completed=appts.filter(Appointment.status == AppointmentStatus.COMPLETED).count(),
                upcoming=appts.filter(Appointment.status == AppointmentStatus.SCHEDULED).count(),
            )
        )

    # --- 14 day appointment volume trend ---
    trend: list[TrendPoint] = []
    today = datetime.now(timezone.utc).date()
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        count = (
            db.query(Appointment)
            .filter(Appointment.scheduled_at >= day_start, Appointment.scheduled_at < day_end)
            .count()
        )
        trend.append(TrendPoint(label=day.strftime("%b %d"), value=count))

    return DashboardSummary(
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_departments=total_departments,
        total_appointments=total_appointments,
        completed_appointments=completed,
        cancelled_appointments=cancelled,
        no_show_appointments=no_show,
        scheduled_appointments=scheduled,
        no_show_rate_percent=no_show_rate,
        cancellation_rate_percent=cancellation_rate,
        department_workload=department_workload,
        doctor_workload=doctor_workload,
        appointment_trend_last_14_days=trend,
    )
