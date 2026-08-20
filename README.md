<div align="center">

# MediFlow AI

**Hospital Operations & Patient Flow Intelligence Platform**

A production-style, full-stack hospital operations system with real-time analytics, waiting-time tracking, and a machine-learning appointment no-show prediction pipeline.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![License](https://img.shields.io/badge/status-active--development-yellow)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Database Schema](#database-schema)
- [Authentication & Security](#authentication--security)
- [Machine Learning](#machine-learning)
- [API Documentation](#api-documentation)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Developer](#developer)

---

## Overview

**MediFlow AI** is a hospital operations and patient-flow intelligence platform built to address a genuine operational problem: hospitals routinely lose visibility into appointment cancellations, no-shows, doctor workload, and patient waiting times because this data is scattered across manual processes rather than centralized and analyzed.

The system is a single, integrated application — not a demo — with a PostgreSQL-backed FastAPI service exposing a versioned REST API, a React/TypeScript frontend consuming that API, and a data-science/ML layer that computes real analytics and predicts appointment no-show risk from live operational data.

It is designed for four roles inside a hospital: **Admin**, **Hospital Manager**, **Doctor**, and **Staff**, with authorization enforced server-side (not just hidden in the UI) at every protected endpoint.

**Core capabilities:**
- Patient, doctor, department, and appointment management with real CRUD operations
- A live operational dashboard where every KPI is computed from the database on each request
- Waiting-time tracking via patient check-in/consultation-start timestamps
- Descriptive statistics, peak-period analysis, and cancellation/no-show drill-downs (pandas/NumPy)
- Data-quality auditing (missing values, duplicates, invalid dates, outliers)
- Exploratory data analysis charts rendered server-side with Matplotlib/Seaborn
- A scikit-learn no-show risk pipeline comparing Logistic Regression, Decision Tree, Random Forest, and optionally XGBoost, with cross-validation and a live prediction endpoint
- Transparent linear-trend appointment demand forecasting
- Real threshold-based operational alerts
- Filterable operational reports with CSV export
- Full light/dark theming across the entire application

---

## Architecture

```mermaid
flowchart TD
    A[User Browser] --> B["React + TypeScript Frontend<br/>(Vite, React Router, Recharts, Axios)"]
    B -->|REST / JSON over HTTPS| C["FastAPI Backend<br/>/api/v1"]
    C --> D[API Routes Layer]
    D --> E[Service Layer<br/>business logic]
    E --> F["SQLAlchemy ORM"]
    F --> G[(PostgreSQL 16)]
    E --> H["Data Science / ML Layer<br/>Pandas, NumPy, Matplotlib, Seaborn"]
    H --> I["Scikit-learn Pipeline<br/>Logistic Regression, Decision Tree,<br/>Random Forest, XGBoost (optional)"]
    I --> J["Persisted Model<br/>(joblib artifact)"]
    C --> K["JWT Auth + RBAC<br/>python-jose, passlib/bcrypt"]
    F --> L["Alembic Migrations"]
```

**Request flow:** the frontend calls the backend exclusively through a single Axios client (`frontend/src/api/client.ts`) that attaches the JWT bearer token to every request. The FastAPI app (`backend/app/main.py`) mounts one aggregated router (`backend/app/api/routes/__init__.py`) under the `/api/v1` prefix. Each route delegates to a service module (`backend/app/services/`) that performs the actual SQLAlchemy queries and business rules (e.g. doctor double-booking conflict checks) — routes themselves stay thin. The data-science/ML layer (`backend/app/ml/`) is decoupled from the HTTP layer: it operates on plain pandas DataFrames built from live database rows, so it can be called from routes, tests, or scripts identically.

**Authentication flow:** `POST /api/v1/auth/login-json` verifies credentials with bcrypt and issues a JWT (HS256, `python-jose`) carrying the user's id and role. Every protected route depends on `get_current_user` (decodes and validates the token, loads the user) or `require_roles(...)` (additionally checks the user's role against an allow-list) — both defined once in `backend/app/api/deps.py` and reused everywhere.

---

## Project Structure

```text
mediflow/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, exception handlers, startup
│   │   ├── core/
│   │   │   ├── config.py            # pydantic-settings Settings (env-driven, no hardcoded secrets)
│   │   │   ├── security.py          # JWT creation/verification, bcrypt hashing
│   │   │   └── logging_config.py    # centralized logging setup
│   │   ├── db/
│   │   │   ├── session.py           # SQLAlchemy engine + session factory
│   │   │   ├── base_class.py        # declarative Base + TimestampMixin
│   │   │   └── init_db.py           # table creation + admin/department seeding
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py, patient.py, doctor.py, department.py
│   │   │   ├── appointment.py, audit_log.py, enums.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/                # Business logic + DB access (no HTTP concerns)
│   │   │   ├── auth_service.py, patient_service.py, doctor_service.py
│   │   │   ├── department_service.py, appointment_service.py
│   │   │   ├── dashboard_service.py, alerts_service.py
│   │   ├── api/
│   │   │   ├── deps.py              # get_current_user, require_roles dependencies
│   │   │   └── routes/              # auth, patients, doctors, departments, appointments,
│   │   │                            # dashboard, analytics, ml, reports
│   │   └── ml/                      # Data science / ML layer
│   │       ├── data_pipeline.py     # cleaning, descriptive stats, waiting-time/peak analysis
│   │       ├── data_quality.py      # missing values, duplicates, outliers, quality score
│   │       ├── eda.py               # Matplotlib/Seaborn charts -> base64 PNG
│   │       ├── forecasting.py       # linear-trend + weekly-seasonality demand forecast
│   │       └── noshow_model.py      # multi-model comparison, CV, evaluation, persistence
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 0001_initial_schema.py            # base schema (all core tables)
│   │       └── 0002_appointment_waiting_time.py  # additive: checked_in_at / started_at
│   ├── tests/                       # pytest suite (8 files, 41 test cases)
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # client.ts (Axios + interceptors), endpoints.ts
│   │   ├── context/                 # AuthContext, ThemeContext
│   │   ├── components/              # Sidebar, Topbar, Modal, StatCard, ProtectedRoute, ...
│   │   ├── pages/                   # Login, Dashboard, Patients, Appointments, Doctors,
│   │   │                            # Departments, Analytics, Predictions, Reports, Settings
│   │   └── styles/global.css        # design system, light/dark theme variables
│   ├── public/logo.png
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf                   # SPA fallback + API reverse proxy for production
│   └── Dockerfile
├── docker-compose.yml                # postgres + backend + frontend
├── README.md
├── VERIFICATION_REPORT.md            # Phase 0 verification notes
├── PHASE1_VERIFICATION_REPORT.md     # Phase 1 verification notes
├── FINAL_VERIFICATION_REPORT.md      # Final full-system verification notes
└── .gitignore
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| **Python 3.12** | Application language |
| **FastAPI 0.115** | REST API framework — routing, dependency injection, OpenAPI docs |
| **Pydantic v2 / pydantic-settings** | Request/response validation and environment-driven configuration |
| **SQLAlchemy 2.0** | ORM mapping Python models to PostgreSQL tables |
| **Alembic** | Version-controlled database schema migrations |
| **python-jose** | JWT creation and verification for authentication |
| **passlib[bcrypt]** | Password hashing |
| **uvicorn** | ASGI server |

### Database

| Technology | Purpose |
|---|---|
| **PostgreSQL 16** | Primary relational database (via `postgres:16-alpine` in Docker) |
| **psycopg2-binary** | PostgreSQL driver for SQLAlchemy |
| **Alembic** | Schema migration/versioning system |

### Frontend

| Technology | Purpose |
|---|---|
| **React 18** | UI library |
| **TypeScript 5.5** | Static typing across the frontend |
| **Vite** | Dev server and production build tool |
| **React Router 6** | Client-side routing |
| **Axios** | HTTP client with JWT-attaching interceptors |
| **Recharts** | Interactive dashboard/analytics charts |
| **Custom CSS design system** (`global.css`) | Light/dark theming via CSS variables, no UI framework dependency |

### AI / Machine Learning

| Technology | Purpose |
|---|---|
| **scikit-learn 1.5** | Logistic Regression, Decision Tree, Random Forest classifiers; `StratifiedKFold` cross-validation; `ColumnTransformer` + `OneHotEncoder` preprocessing pipeline |
| **XGBoost 2.1** | Optional fourth model in the comparison (gracefully skipped if not installed) |
| **joblib** | Trained pipeline persistence/loading |

### Data Science

| Technology | Purpose |
|---|---|
| **pandas** | Data loading, cleaning, feature engineering, group-by analytics |
| **NumPy** | Descriptive statistics (mean, median, std, percentiles), linear-trend forecasting math |
| **Matplotlib / Seaborn** | Server-rendered EDA charts (headless `Agg` backend), output as base64 PNG |

### Development & Testing Tools

| Technology | Purpose |
|---|---|
| **pytest / pytest-cov / httpx** | Backend test suite (uses FastAPI's `TestClient` against an in-memory SQLite database) |
| **Docker / docker-compose** | Containerized PostgreSQL + backend + frontend orchestration |
| **nginx** | Serves the built frontend and reverse-proxies `/api/` to the backend container in production |

---

## Features

### Authentication & Authorization
JWT-based login (`OAuth2PasswordBearer` scheme) with bcrypt password hashing. Four roles — `ADMIN`, `HOSPITAL_MANAGER`, `DOCTOR`, `STAFF` — enforced on the backend via a `require_roles(...)` dependency on every write/delete route, not merely hidden in the UI. New staff accounts can only be registered by an `ADMIN`.

### Patient Management
Full CRUD for patient records (name, date of birth, gender, contact info, blood type, status, notes) with search by name, email, or phone, and safeguards against deleting a patient with existing appointment history.

### Doctor Management
CRUD for doctor records with department assignment, specialty, daily appointment capacity, and active/inactive status; deletion is blocked while a doctor has scheduled appointments.

### Department Management
CRUD for hospital departments with live doctor-count and appointment-count statistics per department; deletion is blocked while doctors are assigned.

### Appointment Management
Scheduling with genuine double-booking conflict detection (overlapping time-window checks per doctor), status lifecycle (`SCHEDULED` → `COMPLETED` / `CANCELLED` / `NO_SHOW`), and check-in/consultation-start actions that feed real waiting-time analytics.

### Operational Dashboard
Every figure — total patients, appointments, completed/cancelled/no-show counts, no-show rate, cancellation rate, department workload, doctor workload, 14-day appointment trend — is computed from a live SQLAlchemy query at request time. An Alerts panel surfaces real threshold-based warnings.

### Analytics
Descriptive statistics (mean/median/std/percentiles) on appointment duration, weekday distribution, waiting-time analysis (mean/median/p90 by department and doctor), peak-period detection (busiest weekday/hour), and cancellation/no-show drill-downs by department and doctor.

### Data Quality
An audit covering missing values, duplicate patient records (matched on name + date of birth), invalid/implausible dates of birth, inconsistent blood-type values, and IQR-based statistical outlier detection on appointment durations — with a composite quality score.

### Exploratory Data Analysis (EDA)
Server-rendered Matplotlib/Seaborn charts — appointment-duration histogram, weekday-by-hour heatmap, and department/status stacked breakdown — delivered to the frontend as base64-encoded PNGs.

### Machine Learning — No-Show Prediction
A full pipeline (clean → engineer features → split → preprocess → train → cross-validate → evaluate → select → persist → infer) comparing Logistic Regression, Decision Tree, Random Forest, and optionally XGBoost. Reports accuracy, precision, recall, F1, ROC-AUC, and a confusion matrix per model, selects the best by test-set F1, and exposes a live `/ml/predict-no-show` endpoint.

### Demand Forecasting
A transparent linear-trend plus weekly-seasonality forecast of appointment volume (overall or per-department), reporting fit quality (R²) and explicit limitations rather than false confidence.

### Operational Alerts
Real, threshold-based alerts (high no-show rate, high cancellation rate, high average wait time, doctor overload, low data-quality score) — no random or placeholder alerts.

### Reports
Filterable appointment reports (status, department, doctor, date range) with aggregate summaries and client-side CSV export.

### Audit Logging
An `audit_logs` table records actor, action, entity type/id, and details for traceability of sensitive operations.

### Light / Dark Mode
Every page, form, table, chart, and modal supports both themes via CSS custom properties, with the preference persisted in `localStorage`.

---

## Database Schema

```mermaid
erDiagram
    USERS ||--o| DOCTORS : "may link to"
    USERS ||--o{ AUDIT_LOGS : performs
    USERS ||--o{ APPOINTMENTS : "created_by"
    DEPARTMENTS ||--o{ DOCTORS : employs
    DEPARTMENTS ||--o{ APPOINTMENTS : hosts
    DOCTORS ||--o{ APPOINTMENTS : handles
    PATIENTS ||--o{ APPOINTMENTS : books

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        enum role
        bool is_active
    }
    DEPARTMENTS {
        int id PK
        string name UK
        string description
        string location
    }
    DOCTORS {
        int id PK
        string full_name
        string specialty
        string email UK
        string phone
        bool is_active
        int daily_capacity
        int department_id FK
        int user_id FK
    }
    PATIENTS {
        int id PK
        string first_name
        string last_name
        date date_of_birth
        enum gender
        string phone
        string email
        string blood_type
        enum status
    }
    APPOINTMENTS {
        int id PK
        int patient_id FK
        int doctor_id FK
        int department_id FK
        datetime scheduled_at
        int duration_minutes
        enum status
        string reason
        datetime checked_in_at
        datetime started_at
        int created_by_id FK
    }
    AUDIT_LOGS {
        int id PK
        int actor_id FK
        string action
        string entity_type
        int entity_id
        string details
    }
```

**Tables:** `users`, `departments`, `doctors`, `patients`, `appointments`, `audit_logs`.

**Enumerations:** `user_role` (`ADMIN`, `HOSPITAL_MANAGER`, `DOCTOR`, `STAFF`), `appointment_status` (`SCHEDULED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`), `patient_status` (`ACTIVE`, `DISCHARGED`, `INACTIVE`), `gender` (`MALE`, `FEMALE`, `OTHER`, `UNSPECIFIED`).

**Foreign key behavior:** `appointments.patient_id` cascades on delete; `appointments.doctor_id` and `appointments.department_id` are `RESTRICT`; `doctors.user_id`, `appointments.created_by_id`, and `audit_logs.actor_id` are `SET NULL` on delete.

**Indexes:** on `users.email`, `departments.name`, `patients.email`, `appointments.scheduled_at`, `appointments.status`, plus composite indexes on `appointments (doctor_id, scheduled_at)` and `appointments (patient_id)`.

**Migrations:**
- `0001_initial_schema.py` — creates all base tables, enums, and indexes.
- `0002_appointment_waiting_time.py` — additive-only migration adding nullable `checked_in_at` and `started_at` columns to `appointments` for waiting-time tracking; no existing column was altered or dropped.

---

## Authentication & Security

- **Login:** `POST /api/v1/auth/login` (OAuth2 form-encoded, for Swagger UI) and `POST /api/v1/auth/login-json` (JSON, used by the frontend) both verify credentials via `authenticate_user()` and issue a JWT.
- **Password hashing:** bcrypt via `passlib.CryptContext`.
- **Token mechanism:** JWT (HS256, `python-jose`) containing `sub` (user id), `role`, and `exp`, signed with `SECRET_KEY` and expiring after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60).
- **Token verification:** `get_current_user` (in `app/api/deps.py`) decodes the bearer token on every protected request and loads the corresponding active user; invalid/expired tokens return `401`.
- **Role-based access control:** `require_roles(*roles)` is a dependency factory used on every write/delete route to restrict it to specific roles; violations return `403`.
- **Registration:** `POST /api/v1/auth/register` is itself restricted to `ADMIN` — self-service signup is intentionally not exposed.
- **Audit logging:** the `AuditLog` model/table exists for recording actor/action/entity traceability.
- **CORS:** configured via the `CORS_ORIGINS` environment variable (comma-separated list), applied through FastAPI's `CORSMiddleware` — not hardcoded to a single origin.
- **Centralized error handling:** dedicated exception handlers for `RequestValidationError` (422), `IntegrityError` (409), `SQLAlchemyError` (500), and a catch-all handler — the API never leaks raw stack traces to the client.
- **No secrets in source:** `backend/.env.example` ships only placeholder values; `.gitignore` excludes `.env` (only `.env.example` is tracked).

---

## Machine Learning

**Problem:** predict the probability that a scheduled appointment will result in a `NO_SHOW`.

**Models compared** (`backend/app/ml/noshow_model.py`):
- Logistic Regression (`class_weight="balanced"`)
- Decision Tree (`max_depth=6`, `class_weight="balanced"`)
- Random Forest (`n_estimators=150`, `max_depth=8`, `class_weight="balanced"`)
- XGBoost — included only if the optional dependency is installed; the comparison degrades gracefully without it

**Features** (`FEATURE_COLUMNS`): `department`, `weekday`, `hour_of_day`, `duration_minutes`, `patient_prior_appointment_count`, `patient_prior_no_show_rate`. Categorical features (`department`, `weekday`) are one-hot encoded inside the same `sklearn.Pipeline` that is persisted, so training and inference always use identical preprocessing.

**Data-leakage safeguard:** the two patient-history features are computed strictly from each patient's chronologically **prior** appointments only (`sort_values` + `groupby` + `shift(1)` + `expanding()`), so the model never sees information about the appointment it is predicting or about that patient's future.

**Pipeline stages:** clean data → engineer features → stratified train/test split → `StratifiedKFold` cross-validation on the training partition → fit each candidate model → evaluate on the held-out test partition (accuracy, precision, recall, F1, ROC-AUC, confusion matrix) → select the best model by test-set F1 (ROC-AUC as tiebreaker) → persist with `joblib` → serve via the prediction endpoint.

**Safeguards against a meaningless model:** training requires at least 30 labeled (`COMPLETED`/`NO_SHOW`) appointments (`min_samples=30`); below that, `/ml/train` returns a clear explanation instead of fabricating a model. Class imbalance is detected and reported (`positive_rate < 15%` or `> 85%` flags `is_imbalanced: true`).

**Model artifacts:** persisted to `backend/app/ml/artifacts/noshow_model.joblib` and `noshow_model_metrics.json` (both git-ignored — regenerated by training, not committed).

**Prediction endpoint:** `POST /api/v1/ml/predict-no-show` loads the persisted pipeline, builds the identical feature set from the request payload, and returns a probability plus a `LOW`/`MEDIUM`/`HIGH` risk tier. If no model has been trained yet, it returns `409 Conflict` with a clear message rather than a server error.

---

## API Documentation

- **Base URL:** `/api/v1` (configurable via `API_V1_PREFIX`)
- **Interactive docs (Swagger UI):** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`
- **OpenAPI schema:** `http://localhost:8000/api/openapi.json`
- **Health check:** `GET /api/health`

### Authentication

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/login` | OAuth2 form-encoded login (Swagger-compatible) | Not required |
| POST | `/api/v1/auth/login-json` | JSON login, used by the frontend | Not required |
| POST | `/api/v1/auth/register` | Create a new staff account | `ADMIN` only |
| GET | `/api/v1/auth/me` | Get the current authenticated user | Required |

### Patients

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/patients` | List/search patients (paginated) | Required |
| GET | `/api/v1/patients/{id}` | Get a patient | Required |
| POST | `/api/v1/patients` | Create a patient | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF` |
| PUT | `/api/v1/patients/{id}` | Update a patient | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF` |
| DELETE | `/api/v1/patients/{id}` | Delete a patient (blocked if appointment history exists) | `ADMIN`, `HOSPITAL_MANAGER` |

### Doctors

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/doctors` | List doctors (filterable by department) | Required |
| GET | `/api/v1/doctors/{id}` | Get a doctor | Required |
| POST | `/api/v1/doctors` | Create a doctor | `ADMIN`, `HOSPITAL_MANAGER` |
| PUT | `/api/v1/doctors/{id}` | Update a doctor | `ADMIN`, `HOSPITAL_MANAGER` |
| DELETE | `/api/v1/doctors/{id}` | Delete a doctor (blocked if scheduled appointments exist) | `ADMIN`, `HOSPITAL_MANAGER` |

### Departments

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/departments` | List departments with live stats | Required |
| GET | `/api/v1/departments/{id}` | Get a department | Required |
| POST | `/api/v1/departments` | Create a department | `ADMIN`, `HOSPITAL_MANAGER` |
| PUT | `/api/v1/departments/{id}` | Update a department | `ADMIN`, `HOSPITAL_MANAGER` |
| DELETE | `/api/v1/departments/{id}` | Delete a department (blocked if doctors assigned) | `ADMIN` only |

### Appointments

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/appointments` | List/filter appointments | Required |
| GET | `/api/v1/appointments/{id}` | Get an appointment | Required |
| POST | `/api/v1/appointments` | Create an appointment (conflict-checked) | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF`, `DOCTOR` |
| PUT | `/api/v1/appointments/{id}` | Update an appointment | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF`, `DOCTOR` |
| POST | `/api/v1/appointments/{id}/cancel` | Cancel a scheduled appointment | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF`, `DOCTOR` |
| POST | `/api/v1/appointments/{id}/complete` | Mark completed | `ADMIN`, `HOSPITAL_MANAGER`, `DOCTOR` |
| POST | `/api/v1/appointments/{id}/check-in` | Record patient arrival | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF`, `DOCTOR` |
| POST | `/api/v1/appointments/{id}/start` | Record consultation start | `ADMIN`, `HOSPITAL_MANAGER`, `DOCTOR` |
| POST | `/api/v1/appointments/{id}/no-show` | Mark as a no-show | `ADMIN`, `HOSPITAL_MANAGER`, `STAFF`, `DOCTOR` |
| DELETE | `/api/v1/appointments/{id}` | Delete an appointment | `ADMIN` only |

### Dashboard & Analytics

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/dashboard/summary` | Live operational KPIs | Required |
| GET | `/api/v1/analytics/appointment-statistics` | Descriptive stats + weekday distribution | Required |
| GET | `/api/v1/analytics/waiting-time` | Waiting-time analysis | Required |
| GET | `/api/v1/analytics/peak-periods` | Busiest weekday/hour | Required |
| GET | `/api/v1/analytics/cancellation-no-show` | Cancellation/no-show by department & doctor | Required |
| GET | `/api/v1/analytics/data-quality` | Data-quality audit | Required |
| GET | `/api/v1/analytics/eda-charts` | Matplotlib/Seaborn charts (base64 PNG) | Required |
| GET | `/api/v1/analytics/forecast` | Appointment demand forecast | Required |
| GET | `/api/v1/analytics/alerts` | Real threshold-based alerts | Required |

### Machine Learning

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| POST | `/api/v1/ml/train` | Train & compare no-show models, persist the best | `ADMIN`, `HOSPITAL_MANAGER` |
| GET | `/api/v1/ml/model-info` | Metrics/comparison from the last training run | Required |
| POST | `/api/v1/ml/predict-no-show` | Real-time no-show risk prediction | Required |

### Reports

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/reports/appointments` | Filterable appointment report + summary | Required |

---

## Prerequisites

### Required Software

| Requirement | Version used in this project |
|---|---|
| Python | 3.12 (as used in `backend/Dockerfile`, `python:3.12-slim`) |
| Node.js | Version not explicitly pinned in the project; use a current LTS release compatible with Vite 5 / TypeScript 5.5 |
| npm | Version not explicitly pinned in the project; ships with your Node.js installation |
| PostgreSQL | 16 (as used in `docker-compose.yml`, `postgres:16-alpine`) |
| Docker & Docker Compose | Recommended path — required if you want to run `docker compose up` |
| Git | For cloning/version control |

Operating system: the project is OS-agnostic (pure Python/Node/Docker); this README includes both Windows and Linux/macOS setup commands.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and adjust as needed. All variables below are actually read by `backend/app/core/config.py`.

```env
# --- Application ---
APP_NAME=MediFlow AI
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

# --- Security ---
SECRET_KEY=change-this-to-a-long-random-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

# --- Database ---
DATABASE_URL=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# --- CORS ---
CORS_ORIGINS=

# --- Seed admin account (created automatically on first backend startup) ---
SEED_ADMIN_EMAIL=
SEED_ADMIN_PASSWORD=
```

| Variable | Purpose |
|---|---|
| `APP_NAME` | Displayed in the FastAPI OpenAPI title |
| `ENVIRONMENT` / `DEBUG` | Controls log verbosity |
| `API_V1_PREFIX` | Prefix under which all API routes are mounted |
| `SECRET_KEY` | JWT signing key — **must** be changed to a long random value in any real deployment |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry duration |
| `ALGORITHM` | JWT signing algorithm (HS256) |
| `DATABASE_URL` | SQLAlchemy connection string; the `db` hostname is used inside `docker-compose`, use `localhost` for a manually-run PostgreSQL instance |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Used both by the `db` container and to construct `DATABASE_URL` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | Credentials for the administrator account auto-created on first startup |

> Never commit a real `.env` file. `.gitignore` already excludes it; only `.env.example` (with placeholder values) is tracked.

---

## Installation

### Step 1 — Extract / Clone the Project

```bash
git clone <your-repo-url> mediflow-ai
cd mediflow-ai
```

### Step 2 — Configure Environment Variables

```bash
cp backend/.env.example backend/.env
# edit backend/.env - at minimum change SECRET_KEY before any real deployment
```

### Step 3 — Choose a Setup Path

- **Docker (recommended)** — provisions PostgreSQL, backend, and frontend together. Skip to [Running the Application](#running-the-application).
- **Manual/local setup** — follow Steps 4-7 below.

### Step 4 — Install Backend Dependencies

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 5 — Configure PostgreSQL

Create the database and user referenced in `backend/.env` (defaults: user `mediflow`, database `mediflow`):

```sql
CREATE USER mediflow WITH PASSWORD 'mediflow_password';
CREATE DATABASE mediflow OWNER mediflow;
```

Then, in `backend/.env`, point `DATABASE_URL` at your local instance instead of the Docker `db` hostname:

```env
DATABASE_URL=postgresql+psycopg2://mediflow:mediflow_password@localhost:5432/mediflow
```

### Step 6 — Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This applies `0001_initial_schema.py` (base schema) followed by `0002_appointment_waiting_time.py` (waiting-time columns).

### Step 7 — Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## Running the Application

### Startup Sequence

```text
1. Start PostgreSQL (or let docker-compose start it for you)
2. Configure backend/.env
3. Run Alembic migrations (docker-compose runs this automatically on backend startup)
4. Start the backend
5. Start the frontend
6. Open http://localhost:5173 (dev) or http://localhost:3000 (Docker)
```

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

- Backend API: `http://localhost:8000` (docs at `/api/docs`)
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

The backend container automatically runs `alembic upgrade head` before starting `uvicorn` (see `backend/Dockerfile`), and seeds one `ADMIN` account plus five default departments (General Medicine, Emergency, Cardiology, Pediatrics, Orthopedics) on first startup.

### Option B — Manual, Two Terminals

**Terminal 1 — Backend**

```bash
cd backend
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

Then open the URL Vite prints (typically `http://localhost:5173`).

### Default Login

| Field | Value |
|---|---|
| Email | value of `SEED_ADMIN_EMAIL` in your `.env` |
| Password | value of `SEED_ADMIN_PASSWORD` in your `.env` |

---

## Testing

**Framework:** pytest, using FastAPI's `TestClient` against an in-memory SQLite database (`backend/tests/conftest.py`) — fast and dependency-free for CI, while the application code itself contains no PostgreSQL-only syntax.

**Location:** `backend/tests/` — 8 files, 41 test cases:

| File | Covers |
|---|---|
| `test_auth.py` | Login, token issuance, registration, role restriction |
| `test_patients.py` | Patient CRUD, search, validation |
| `test_doctors_departments.py` | Doctor/department CRUD, delete constraints |
| `test_appointments.py` | Appointment CRUD, double-booking conflict detection, cancellation |
| `test_waiting_time.py` | Check-in/start flow, wait-time computation |
| `test_dashboard.py` | Dashboard KPIs reflect real writes |
| `test_analytics_phase1.py` | Waiting-time, peak-period, data-quality, EDA, forecast, alert endpoints |
| `test_ml_and_reports.py` | ML train/predict graceful degradation, filtered reports |

**Run the tests:**

```bash
cd backend
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

---

## Troubleshooting

**`sqlalchemy.exc.OperationalError` / cannot connect to database**
Confirm PostgreSQL is running and `DATABASE_URL` in `backend/.env` matches your setup — use `db` as the host only when running via `docker-compose`; use `localhost` for a manually-run PostgreSQL instance.

**`alembic upgrade head` fails with "target database is not up to date"**
Run `alembic current` to see the applied revision, then `alembic upgrade head` again; ensure no manual schema changes were made outside of Alembic.

**Port already in use (`8000`, `5173`/`3000`, or `5432`)**
Stop the conflicting process, or change the exposed port mapping in `docker-compose.yml` / pass `--port` to `uvicorn`/`vite`.

**Frontend requests fail with CORS errors**
Ensure the frontend's origin is listed in `CORS_ORIGINS` in `backend/.env` (comma-separated, no trailing slash).

**`ModuleNotFoundError` for a Python package**
Confirm the virtual environment is activated and `pip install -r requirements.txt` completed without errors.

**`POST /ml/predict-no-show` returns 409**
No model has been trained yet, or there isn't enough labeled appointment history. Call `POST /ml/train` first — it requires at least 30 `COMPLETED`/`NO_SHOW` appointments in the database.

**Windows: `.\.venv\Scripts\Activate.ps1` fails with an execution-policy error**
Run PowerShell as Administrator and execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry activation.

---

## Limitations

- The no-show ML model requires a minimum of 30 labeled appointments before it will train; below that, the training endpoint reports why rather than producing an unreliable model.
- Waiting-time analytics depend on staff actually using the Check-in/Start actions; historical or API-created appointments without those calls simply show no wait-time data.
- Demand forecasting requires at least 14 days of appointment history and does not account for holidays or external events — it is a planning aid, not a guarantee.
- Doctor login accounts can be created by an admin, but doctor-specific self-service views are not yet built.
- No email/SMS notifications, file/document uploads, or multi-branch support.
- No production-grade rate limiting or secrets-manager integration is configured.

---

## Developer

**Rana Umar Draz**
