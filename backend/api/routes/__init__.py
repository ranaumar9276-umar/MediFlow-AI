from fastapi import APIRouter

from app.api.routes import analytics, appointments, auth, dashboard, departments, doctors, ml, patients, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(doctors.router)
api_router.include_router(departments.router)
api_router.include_router(appointments.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(ml.router)
api_router.include_router(reports.router)
