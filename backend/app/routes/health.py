from fastapi import APIRouter
from app.mt5_client import mt5_client
from app.ai_client import ai_client
from app.hermes_client import hermes_client

router = APIRouter()


@router.get("/health")
async def health_check():
    mt5_connected = mt5_client.is_connected

    # Check Hermes Agent health
    hermes_status = await hermes_client.health_check()

    return {
        "status": "ok" if mt5_connected else "degraded",
        "mt5_connected": mt5_connected,
        "ai_available": ai_client.is_available,
        "hermes_agent": {
            "enabled": hermes_client.enabled,
            "url": hermes_client.url if hermes_client.enabled else None,
            "connected": hermes_status,
            "fallback_to_direct_ai": hermes_client.fallback_enabled,
        },
    }
