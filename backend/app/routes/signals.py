from fastapi import APIRouter, HTTPException
from app.mt5_client import mt5_client
from app.multi_timeframe_analysis import multi_timeframe_analysis, evaluate_signal_candidate
from app.confirmation import check_confirmation, record_candidate, get_history
from app.pullback_entry import check_pullback_entry
from app.config import settings
from app.database import async_session
from app.models import Signal
from sqlalchemy import select

router = APIRouter(prefix="/api")

# In-memory signal state per symbol
_signal_state: dict = {}


def find_symbol(symbol: str) -> str:
    for s in settings.symbol_list:
        if s.lower() == symbol.lower():
            return s
    return ""


@router.get("/signals/{symbol}")
async def get_signal(symbol: str):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")

    state = _signal_state.get(matched)
    if state:
        return state

    async with async_session() as session:
        result = await session.execute(
            select(Signal)
            .where(Signal.symbol == matched)
            .order_by(Signal.created_at.desc())
            .limit(1)
        )
        db_signal = result.scalar_one_or_none()
        if db_signal:
            return {
                "symbol": db_signal.symbol,
                "status": db_signal.status,
                "direction": db_signal.direction,
                "confidence": db_signal.confidence,
                "reasons": db_signal.reason_json or [],
                "h1_trend": db_signal.h1_trend,
                "m30_trend": db_signal.m30_trend,
                "m15_trend": db_signal.m15_trend,
                "m5_trend": db_signal.m5_trend,
                "market_condition": db_signal.market_condition,
                "rsi14": db_signal.rsi14,
                "atr14": db_signal.atr14,
                "adx14": db_signal.adx14,
                "macd_histogram": db_signal.macd_histogram,
                "ema_distance_atr_ratio": db_signal.ema_distance_atr_ratio,
                "spread": db_signal.spread,
                "nearest_support": db_signal.nearest_support,
                "nearest_resistance": db_signal.nearest_resistance,
                "pullback_status": db_signal.pullback_status,
                "rejection_candle_status": db_signal.rejection_candle_status,
                "blocked_reasons": db_signal.blocked_reasons_json or [],
                "warnings": db_signal.warnings_json or [],
                "timeframe": db_signal.timeframe,
                "candle_time": db_signal.candle_time.isoformat() if db_signal.candle_time else None,
                "created_at": db_signal.created_at.isoformat() if db_signal.created_at else None,
            }

    return {
        "symbol": matched,
        "status": "WAIT",
        "direction": None,
        "confidence": 0,
        "reasons": ["No analysis data yet"],
    }


@router.get("/analysis/{symbol}")
async def get_analysis(symbol: str):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")

    analysis = multi_timeframe_analysis(matched)
    if not analysis:
        raise HTTPException(status_code=503, detail=f"Not enough data for {matched}. MT5 may not be connected or market is closed.")

    tick = mt5_client.get_tick(matched)
    spread = tick["spread"] if tick else 0
    max_spread = settings.get_max_spread(matched)

    candidate = evaluate_signal_candidate(analysis, spread, max_spread)

    m5 = analysis["m5"]
    fib = analysis.get("fibonacci", {})

    # Pullback check
    pullback = {"ready": False, "status": "NOT_CHECKED"}
    if candidate.get("direction"):
        last_candle = m5.get("last_candle", {})
        pullback = check_pullback_entry(
            candidate["direction"],
            m5["last_close"],
            m5["ema20"],
            m5["atr14"],
            m5.get("highs", []),
            m5.get("lows", []),
            last_candle,
            fib,
        )

    # Build response without raw candle arrays
    def clean_tf(tf):
        return {
            "trend": tf["trend"],
            "ema20": tf["ema20"],
            "ema50": tf["ema50"],
            "rsi14": tf["rsi14"],
            "atr14": tf["atr14"],
            "adx14": tf["adx14"],
            "macd": tf["macd"],
            "ema_distance": tf["ema_distance"],
            "ema_distance_atr_ratio": tf["ema_distance_atr_ratio"],
            "market_condition": tf["market_condition"],
            "support_resistance": tf["support_resistance"],
            "last_close": tf["last_close"],
            "candle_time": tf["candle_time"],
        }

    return {
        "symbol": matched,
        "h1": clean_tf(analysis["h1"]),
        "m30": clean_tf(analysis["m30"]),
        "m15": clean_tf(analysis["m15"]),
        "m5": clean_tf(analysis["m5"]),
        "market_condition": analysis["market_condition"],
        "fibonacci": {k: v for k, v in fib.items() if k != "levels"} if fib.get("valid") else {"valid": False},
        "fibonacci_levels": fib.get("levels", {}),
        "candidate": candidate,
        "pullback": pullback,
        "spread": spread,
        "max_spread": max_spread,
    }
