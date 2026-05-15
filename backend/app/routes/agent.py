from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from app.hermes_client import hermes_client
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/status")
async def get_agent_status() -> Dict[str, Any]:
    """Get Hermes Agent status"""
    return hermes_client.get_status()


@router.post("/trade-analysis")
async def trade_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze trade setup using Hermes Agent.

    This endpoint receives trade analysis data from the frontend/signal engine,
    sends it to Hermes Agent for AI orchestration, and returns the analysis result.

    Hermes Agent is an OpenAI-compatible gateway that calls /v1/chat/completions.
    """
    if not settings.hermes_agent_enabled:
        logger.warning("Hermes Agent is disabled, returning safe fallback")
        return {
            "success": False,
            "source": "hermes_disabled",
            "direction": "WAIT",
            "recommendation": "AVOID",
            "should_create_trade_plan": False,
            "manual_approval_required": True,
            "summary": "Hermes Agent is disabled",
        }

    try:
        result = await hermes_client.trade_analysis(payload)
        return result
    except Exception as e:
        logger.error(f"Trade analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news-analysis")
async def news_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze news impact using Hermes Agent.

    This endpoint sends news context to Hermes Agent for analysis.
    """
    if not settings.hermes_agent_enabled:
        logger.warning("Hermes Agent is disabled, returning safe fallback")
        return {
            "success": False,
            "source": "hermes_disabled",
            "blocked": False,
            "risk_level": "CLEAR",
        }

    try:
        # Prepare system message for news analysis
        system_message = (
            "You are Hermes Agent for news analysis. "
            "Analyze the news context and determine if trading should be blocked. "
            "Return strict JSON only. "
            "If high-impact news is upcoming, recommend blocking trades. "
            "Return: {blocked: bool, risk_level: 'CLEAR'|'CAUTION'|'HIGH', summary: str}"
        )

        import json
        request_body = {
            "model": "hermes-agent",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": json.dumps(payload)},
            ],
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {settings.hermes_agent_api_key}",
            "Content-Type": "application/json",
        }

        import httpx
        async with httpx.AsyncClient(timeout=settings.hermes_agent_timeout_seconds) as client:
            response = await client.post(
                f"{settings.hermes_agent_url}/v1/chat/completions",
                json=request_body,
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(f"Hermes news analysis failed: {response.status_code}")
                return {
                    "success": False,
                    "blocked": False,
                    "risk_level": "CLEAR",
                    "source": "hermes_error",
                }

            response_data = response.json()
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            try:
                result = json.loads(content)
                result["source"] = "hermes_agent"
                return result
            except json.JSONDecodeError:
                logger.error(f"Hermes returned invalid JSON for news analysis")
                return {
                    "success": False,
                    "blocked": False,
                    "risk_level": "CLEAR",
                    "source": "hermes_error",
                }

    except Exception as e:
        logger.error(f"News analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-response")
async def validate_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate AI response against safety rules using Hermes Agent.

    This endpoint sends a proposed trade response to Hermes Agent for validation.
    """
    if not settings.hermes_agent_enabled:
        logger.warning("Hermes Agent is disabled, returning safe fallback")
        return {
            "success": False,
            "source": "hermes_disabled",
            "valid": False,
            "errors": ["Hermes Agent is disabled"],
        }

    try:
        # Prepare system message for validation
        system_message = (
            "You are Hermes Agent for response validation. "
            "Validate the proposed trade response against safety rules. "
            "Return strict JSON only. "
            "Check: direction is BUY/SELL/WAIT, entry_price_source matches direction, "
            "manual_approval_required is true, risk_engine.allowed is respected. "
            "Return: {valid: bool, errors: [str], warnings: [str]}"
        )

        import json
        request_body = {
            "model": "hermes-agent",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": json.dumps(payload)},
            ],
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {settings.hermes_agent_api_key}",
            "Content-Type": "application/json",
        }

        import httpx
        async with httpx.AsyncClient(timeout=settings.hermes_agent_timeout_seconds) as client:
            response = await client.post(
                f"{settings.hermes_agent_url}/v1/chat/completions",
                json=request_body,
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(f"Hermes validation failed: {response.status_code}")
                return {
                    "success": False,
                    "valid": False,
                    "errors": ["Hermes Agent validation failed"],
                    "source": "hermes_error",
                }

            response_data = response.json()
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            try:
                result = json.loads(content)
                result["source"] = "hermes_agent"
                return result
            except json.JSONDecodeError:
                logger.error(f"Hermes returned invalid JSON for validation")
                return {
                    "success": False,
                    "valid": False,
                    "errors": ["Invalid response from Hermes Agent"],
                    "source": "hermes_error",
                }

    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
