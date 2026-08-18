"""
Database bootstrap helper.

In production, schema changes are managed exclusively through Alembic
migrations (see /backend/alembic). This module is only responsible for:
1. Creating tables when running in a fresh dev/test environment
   (guarded - not used when Alembic is the source of truth in CI/CD).
2. Seeding a single ADMIN account from environment variables so the
   application is usable immediately after first boot.
"""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.base_class import Base
from app.db.session import SessionLocal, engine
from app.models import Department, User  # noqa: F401 (ensures models are registered)
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_admin(db: Session) -> None:
    existing = db.query(User).filter(User.email == settings.SEED_ADMIN_EMAIL.lower()).first()
    if existing:
        return
    admin = User(
        email=settings.SEED_ADMIN_EMAIL.lower(),
        hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info("Seeded default admin account: %s", settings.SEED_ADMIN_EMAIL)


def seed_default_departments(db: Session) -> None:
    defaults = [
        ("General Medicine", "Primary care and general consultations"),
        ("Emergency", "Emergency and urgent care"),
        ("Cardiology", "Heart and cardiovascular care"),
        ("Pediatrics", "Care for infants, children and adolescents"),
        ("Orthopedics", "Musculoskeletal system care"),
    ]
    for name, description in defaults:
        if not db.query(Department).filter(Department.name == name).first():
            db.add(Department(name=name, description=description))
    db.commit()


def init_db() -> None:
    create_tables()
    db = SessionLocal()
    try:
        seed_admin(db)
        seed_default_departments(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
