from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from app.ai_client import ai_client
from app.hermes_client import hermes_client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

WIB = timezone(timedelta(hours=7))


def build_ai_payload(symbol: str, analysis: Dict, candidate: Dict, spread: float, tick: Optional[Dict] = None) -> Dict:
    h1 = analysis["h1"]
    m30 = analysis["m30"]
    m15 = analysis["m15"]
    m5 = analysis["m5"]

    bid = tick["bid"] if tick else 0
    ask = tick["ask"] if tick else 0

    payload = {
        "symbol": symbol.replace(".m", ""),
        "current_price": {
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "time": datetime.now(tz=WIB).isoformat(),
        },
        "multi_timeframe": {
            "h1": {
                "trend": h1["trend"],
                "ema20": h1["ema20"],
                "ema50": h1["ema50"],
                "rsi14": h1["rsi14"],
                "atr14": h1["atr14"],
                "last_closed_close": h1["last_close"],
            },
            "m30": {
                "trend": m30["trend"],
                "ema20": m30["ema20"],
                "ema50": m30["ema50"],
                "rsi14": m30["rsi14"],
                "atr14": m30["atr14"],
                "last_closed_close": m30["last_close"],
            },
            "m15": {
                "trend": m15["trend"],
                "ema20": m15["ema20"],
                "ema50": m15["ema50"],
                "rsi14": m15["rsi14"],
                "atr14": m15["atr14"],
                "last_closed_close": m15["last_close"],
            },
            "m5": {
                "trend": m5["trend"],
                "ema20": m5["ema20"],
                "ema50": m5["ema50"],
                "rsi14": m5["rsi14"],
                "atr14": m5["atr14"],
                "last_closed_close": m5["last_close"],
                "last_closed_candle_time": m5.get("candle_time", ""),
            },
        },
        "technical_engine": {
            "candidate": candidate.get("status", "WAIT"),
            "confirmed": candidate.get("status", "").endswith("CONFIRMED"),
            "confidence": candidate.get("confidence", 0),
            "reason": candidate.get("reasons", []),
        },
        "risk_context": {
            "max_spread": settings.get_max_spread(symbol),
            "spread_ok": spread <= settings.get_max_spread(symbol),
            "min_confidence": settings.min_confidence,
            "min_risk_reward": settings.min_risk_reward,
            "manual_approval_required": settings.manual_approval_required,
            "daily_trades_count": 0,
            "max_trades_per_day": settings.max_trades_per_day,
            "daily_loss_percent": 0,
            "max_daily_loss_percent": settings.max_daily_loss_percent,
        },
        "trade_plan_preview": {
            "buy_entry_price": ask,
            "sell_entry_price": bid,
            "note": "Use ask for BUY entry and bid for SELL entry.",
        },
    }

    return payload


async def run_ai_analysis(symbol: str, analysis: Dict, candidate: Dict, spread: float, tick: Optional[Dict] = None, trigger_type: str = "AUTO") -> Optional[Dict]:
    """
    Run AI analysis through Hermes Agent if enabled, otherwise use direct AI client.

    Flow:
    1. If Hermes enabled → send to Hermes Agent (/v1/chat/completions)
    2. If Hermes fails and fallback enabled → use direct AI client
    3. If both fail → return None
    """
    if not ai_client.is_available and not hermes_client.enabled:
        logger.warning("Neither AI client nor Hermes Agent is available")
        return None

    payload = build_ai_payload(symbol, analysis, candidate, spread, tick)

    # Try Hermes Agent first if enabled
    if hermes_client.enabled:
        logger.info(f"Sending AI analysis to Hermes Agent for {symbol}")
        hermes_result = await hermes_client.trade_analysis(payload)

        # Check if Hermes returned a valid response (not fallback)
        if hermes_result.get("source") == "hermes_agent" and hermes_result.get("success"):
            logger.info(f"Hermes Agent analysis successful for {symbol}")
            return _format_ai_response(symbol, hermes_result, payload, trigger_type, source="hermes_agent")

        # If Hermes returned fallback but fallback_to_direct_ai is enabled, try direct AI
        if hermes_result.get("source") in ["direct_ai_fallback", "hermes_safe_fallback"] and hermes_client.fallback_enabled:
            logger.info(f"Hermes fallback triggered, trying direct AI client for {symbol}")
            if ai_client.is_available:
                result = await ai_client.analyze(payload)
                if result:
                    return _format_ai_response(symbol, result["response"], payload, trigger_type, source="direct_ai_fallback", raw_response=result["raw_response"])

        # If Hermes failed completely and no fallback
        if hermes_result.get("source") == "hermes_unavailable":
            logger.warning(f"Hermes Agent unavailable and fallback disabled for {symbol}")
            return None

    # If Hermes not enabled, use direct AI client
    if ai_client.is_available:
        logger.info(f"Using direct AI client for {symbol}")
        result = await ai_client.analyze(payload)
        if result:
            return _format_ai_response(symbol, result["response"], payload, trigger_type, source="direct_ai", raw_response=result["raw_response"])

    logger.error(f"All AI analysis methods failed for {symbol}")
    return None


def _format_ai_response(symbol: str, response: Dict, payload: Dict, trigger_type: str, source: str = "hermes_agent", raw_response: Optional[Dict] = None) -> Dict:
    """Format AI response into standard format"""
    return {
        "success": True,
        "symbol": symbol,
        "trigger_type": trigger_type,
        "ai_source": source,
        "ai_bias": response.get("ai_bias", response.get("final_bias", "NEUTRAL")),
        "direction": response.get("direction", "WAIT"),
        "ai_confidence": response.get("ai_confidence", response.get("confidence", 0)),
        "recommendation": response.get("recommendation", "WAIT"),
        "setup_quality": response.get("setup_quality", "FAIR"),
        "entry_price": response.get("entry_price"),
        "entry_price_source": response.get("entry_price_source", "NONE"),
        "stop_loss": response.get("stop_loss"),
        "take_profit_1": response.get("take_profit_1"),
        "take_profit_2": response.get("take_profit_2"),
        "risk_reward": response.get("risk_reward"),
        "summary": response.get("summary", ""),
        "entry_reason": response.get("entry_reason", ""),
        "risk_warning": response.get("risk_warning", ""),
        "should_create_trade_plan": response.get("should_create_trade_plan", False),
        "manual_approval_required": response.get("manual_approval_required", True),
        "notes": response.get("notes", []),
        "raw_request_json": payload,
        "raw_response_json": raw_response or response,
    }
