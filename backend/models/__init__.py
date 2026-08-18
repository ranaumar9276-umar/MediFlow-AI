"""
Import every model here so that:
1. Alembic's autogenerate can discover all tables via Base.metadata.
2. SQLAlchemy can resolve string-based relationship() references between
   models regardless of import order elsewhere in the app.
"""
from app.db.base_class import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.appointment import Appointment  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

__all__ = ["Base", "User", "Department", "Doctor", "Patient", "Appointment", "AuditLog"]
