from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    doctors: Mapped[list["Doctor"]] = relationship("Doctor", back_populates="department")
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="department"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Department id={self.id} name={self.name}>"
