from fastapi import APIRouter
from app.mt5_client import mt5_client
from app.ai_client import ai_client

router = APIRouter()


@router.get("/health")
async def health_check():
    mt5_connected = mt5_client.is_connected
    return {
        "status": "ok" if mt5_connected else "degraded",
        "mt5_connected": mt5_connected,
        "ai_available": ai_client.is_available,
    }
