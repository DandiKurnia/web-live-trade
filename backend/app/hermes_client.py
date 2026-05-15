import httpx
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class HermesClient:
    """Client untuk komunikasi dengan Hermes Agent (OpenAI-compatible gateway)"""

    def __init__(self):
        self.enabled = settings.hermes_agent_enabled
        self.url = settings.hermes_agent_url
        self.timeout = settings.hermes_agent_timeout_seconds
        self.api_key = settings.hermes_agent_api_key
        self.fallback_enabled = settings.hermes_agent_fallback_to_direct_ai
        self.last_error: Optional[str] = None
        self.last_check: Optional[datetime] = None
        self.is_connected = False

    async def health_check(self) -> bool:
        """Check Hermes Agent health status"""
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.url}/health")
                self.is_connected = response.status_code == 200
                self.last_check = datetime.utcnow()
                self.last_error = None
                logger.info(f"Hermes health check: {response.status_code}")
                return self.is_connected
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            self.last_check = datetime.utcnow()
            logger.error(f"Hermes health check failed: {e}")
            return False

    async def trade_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send trade analysis request to Hermes Agent.
        Hermes is an OpenAI-compatible gateway, so we use /v1/chat/completions endpoint.
        """
        if not self.enabled:
            return self._safe_fallback("Hermes Agent is disabled")

        try:
            # Prepare the system message for Hermes
            system_message = (
                "You are Hermes Agent for trading analysis. "
                "Return strict JSON only. Never execute trades. "
                "Risk Engine is the highest authority. "
                "Never override risk_engine.allowed=false. "
                "If news_context.blocked=true, recommend WAIT or AVOID. "
                "BUY entry must use ASK. SELL entry must use BID. "
                "Manual approval is always required."
            )

            # Prepare the request for OpenAI-compatible endpoint
            request_body = {
                "model": "hermes-agent",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                "stream": False,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.url}/v1/chat/completions",
                    json=request_body,
                    headers=headers,
                )

                if response.status_code != 200:
                    error_msg = f"Hermes returned {response.status_code}: {response.text}"
                    self.last_error = error_msg
                    logger.error(error_msg)
                    return await self._handle_fallback(payload)

                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Parse the JSON response from Hermes
                try:
                    hermes_response = json.loads(content)
                    hermes_response["source"] = "hermes_agent"
                    self.last_error = None
                    return self._validate_response(hermes_response)
                except json.JSONDecodeError as e:
                    error_msg = f"Hermes returned invalid JSON: {e}"
                    self.last_error = error_msg
                    logger.error(error_msg)
                    return self._safe_fallback(error_msg)

        except httpx.TimeoutException:
            error_msg = f"Hermes request timeout after {self.timeout}s"
            self.last_error = error_msg
            logger.error(error_msg)
            return await self._handle_fallback(payload)
        except Exception as e:
            error_msg = f"Hermes request failed: {e}"
            self.last_error = error_msg
            logger.error(error_msg)
            return await self._handle_fallback(payload)

    async def _handle_fallback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fallback when Hermes fails"""
        if self.fallback_enabled:
            logger.info("Falling back to direct AI client")
            return {
                "success": False,
                "source": "direct_ai_fallback",
                "direction": "WAIT",
                "recommendation": "AVOID",
                "should_create_trade_plan": False,
                "manual_approval_required": True,
                "summary": "Hermes Agent unavailable, using direct AI fallback",
            }
        else:
            return {
                "success": False,
                "source": "hermes_unavailable",
                "direction": "WAIT",
                "recommendation": "AVOID",
                "should_create_trade_plan": False,
                "manual_approval_required": True,
                "summary": "Hermes Agent unavailable and fallback disabled",
            }

    def _safe_fallback(self, reason: str) -> Dict[str, Any]:
        """Return safe fallback response"""
        return {
            "success": False,
            "source": "hermes_safe_fallback",
            "final_bias": "NEUTRAL",
            "direction": "WAIT",
            "recommendation": "AVOID",
            "confidence": 0,
            "setup_quality": "POOR",
            "entry_price": None,
            "entry_price_source": "NONE",
            "should_create_trade_plan": False,
            "manual_approval_required": True,
            "summary": f"Hermes Agent is unavailable or returned invalid response. Reason: {reason}",
            "entry_reason": "No entry because AI validation failed.",
            "risk_warning": "Manual review required.",
            "validation": {
                "risk_engine_respected": True,
                "schema_valid": False,
                "news_filter_respected": True,
            },
            "notes": ["Safe fallback activated"],
        }

    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Hermes response against safety rules"""
        errors = []

        # Check required fields
        required_fields = [
            "direction",
            "recommendation",
            "entry_price_source",
            "should_create_trade_plan",
            "manual_approval_required",
        ]
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")

        # Validate direction
        if response.get("direction") not in ["BUY", "SELL", "WAIT"]:
            errors.append(f"Invalid direction: {response.get('direction')}")

        # Validate recommendation
        if response.get("recommendation") not in ["VALID_SETUP", "WATCH", "WAIT", "AVOID"]:
            errors.append(f"Invalid recommendation: {response.get('recommendation')}")

        # Validate entry_price_source
        direction = response.get("direction")
        entry_source = response.get("entry_price_source")

        if direction == "BUY" and entry_source != "ASK":
            errors.append(f"BUY must use ASK, got {entry_source}")
        elif direction == "SELL" and entry_source != "BID":
            errors.append(f"SELL must use BID, got {entry_source}")
        elif direction == "WAIT" and entry_source != "NONE":
            errors.append(f"WAIT must use NONE, got {entry_source}")

        # Validate manual_approval_required is always true
        if response.get("manual_approval_required") is not True:
            errors.append("manual_approval_required must always be true")

        if errors:
            logger.error(f"Hermes response validation failed: {errors}")
            response["validation"]["schema_valid"] = False
            response["notes"] = errors
            return self._safe_fallback("; ".join(errors))

        response["validation"]["schema_valid"] = True
        return response

    def get_status(self) -> Dict[str, Any]:
        """Get Hermes Agent status"""
        return {
            "enabled": self.enabled,
            "url": self.url if self.enabled else None,
            "connected": self.is_connected,
            "timeout_seconds": self.timeout,
            "fallback_to_direct_ai": self.fallback_enabled,
            "last_error": self.last_error,
            "last_check": self.last_check.isoformat() if self.last_check else None,
        }


# Global instance
hermes_client = HermesClient()
