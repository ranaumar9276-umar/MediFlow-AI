"""
Shared pytest fixtures.

Tests run against an in-memory SQLite database rather than PostgreSQL so
they are fast and require no external services in CI. The application
code itself is database-agnostic (plain SQLAlchemy Core/ORM, no
Postgres-only syntax in the ORM layer), so this gives real confidence
that the API/service/DB layers work correctly. Production always runs
against PostgreSQL as configured via DATABASE_URL.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SEED_ADMIN_EMAIL", "admin@mediflow.ai")
os.environ.setdefault("SEED_ADMIN_PASSWORD", "Admin@12345")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.db.session import get_db
import app.models  # noqa: F401 registers models
from app.db.init_db import seed_admin, seed_default_departments
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_admin(db)
    seed_default_departments(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/login-json",
        json={"email": "admin@mediflow.ai", "password": "Admin@12345"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
