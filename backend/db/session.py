"""
SQLAlchemy engine and session factory.

The engine talks to PostgreSQL through the DATABASE_URL defined in the
environment. Session objects are created per-request via the `get_db`
FastAPI dependency and always closed afterwards.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # Only used for lightweight local/test runs; production uses PostgreSQL.
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
