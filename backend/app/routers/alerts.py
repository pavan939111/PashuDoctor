from fastapi import APIRouter, Query
from typing import List, Optional
from app.services.alert_service import get_active_alerts

router = APIRouter()

@router.get("/")
async def list_alerts(state: str, disease: Optional[str] = None):
    """
    Get active disease alerts for a specific state.
    """
    alerts = get_active_alerts(state, disease)
    return {
        "success": True,
        "state": state,
        "alerts": alerts,
        "count": len(alerts)
    }
