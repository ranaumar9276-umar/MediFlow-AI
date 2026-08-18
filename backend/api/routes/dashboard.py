from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import build_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """
    Real-time operational KPIs computed directly from the database.
    Nothing here is hardcoded - every figure is a live query result.
    """
    return build_dashboard_summary(db)
