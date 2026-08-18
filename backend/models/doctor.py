from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Max appointments a doctor can be scheduled for per day - used for workload analytics
    daily_capacity: Mapped[int] = mapped_column(default=12, nullable=False)

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    department: Mapped["Department"] = relationship("Department", back_populates="doctors")

    # Optional link back to the login account for this doctor
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="doctor_profile")

    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="doctor")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Doctor id={self.id} name={self.full_name}>"
