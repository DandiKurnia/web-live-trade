from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from app.ai_client import ai_client
from app.config import settings

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
    if not ai_client.is_available:
        return None

    payload = build_ai_payload(symbol, analysis, candidate, spread, tick)

    result = await ai_client.analyze(payload)

    if not result:
        return None

    response = result["response"]
    return {
        "success": True,
        "symbol": symbol,
        "trigger_type": trigger_type,
        "ai_bias": response.get("ai_bias", "NEUTRAL"),
        "direction": response.get("direction", "WAIT"),
        "ai_confidence": response.get("ai_confidence", 0),
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
        "raw_response_json": result["raw_response"],
    }
