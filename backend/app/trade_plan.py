from typing import Dict, Optional
from app.mt5_client import mt5_client
from app.indicators import find_swing_high, find_swing_low
from app.config import settings
from app.multi_timeframe_analysis import get_closed_candles


def generate_trade_plan(symbol: str, direction: str, confidence: int, signal_id: int, analysis: Dict, analysis_data: Dict = None) -> Optional[Dict]:
    """Generate trade plan with improved ATR-based SL/TP after signal confirmation."""
    tick = mt5_client.get_tick(symbol)
    if not tick:
        return None

    m5 = analysis["m5"]
    atr = m5["atr14"]
    if atr <= 0:
        return None

    # Get recent candles for swing high/low
    candles = get_closed_candles(symbol, "M5", settings.sr_lookback_long)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    if direction == "BUY":
        entry = tick["ask"]

        # Wider SL: use min of ATR-based and swing-based (choose safer/wider)
        atr_sl = entry - settings.atr_sl_multiplier * atr
        swing_low = find_swing_low(lows, settings.sr_lookback_short)
        swing_sl = swing_low - settings.sl_atr_buffer_multiplier * atr if swing_low > 0 else atr_sl
        stop_loss = min(atr_sl, swing_sl)

        risk = entry - stop_loss
        if risk <= 0:
            return None

        tp1 = entry + risk * settings.tp1_r_multiplier
        tp2 = entry + risk * settings.tp2_r_multiplier
        tp3 = entry + risk * settings.tp3_r_multiplier

    elif direction == "SELL":
        entry = tick["bid"]

        # Wider SL: use max of ATR-based and swing-based (choose safer/wider)
        atr_sl = entry + settings.atr_sl_multiplier * atr
        swing_high = find_swing_high(highs, settings.sr_lookback_short)
        swing_sl = swing_high + settings.sl_atr_buffer_multiplier * atr if swing_high > 0 else atr_sl
        stop_loss = max(atr_sl, swing_sl)

        risk = stop_loss - entry
        if risk <= 0:
            return None

        tp1 = entry - risk * settings.tp1_r_multiplier
        tp2 = entry - risk * settings.tp2_r_multiplier
        tp3 = entry - risk * settings.tp3_r_multiplier

    else:
        return None

    sl_distance = abs(entry - stop_loss)
    min_sl_distance = settings.get_min_sl_distance(symbol)
    rr_ratio = (abs(tp1 - entry) / sl_distance) if sl_distance > 0 else 0

    # Get fib zone if available
    fib_zone_low = 0.0
    fib_zone_high = 0.0
    if analysis_data and "fibonacci" in analysis_data:
        fib = analysis_data["fibonacci"]
        fib_zone_low = fib.get("zone_low", 0)
        fib_zone_high = fib.get("zone_high", 0)

    pullback_confirmed = False
    rejection_confirmed = False
    if analysis_data and "pullback" in analysis_data:
        pullback_confirmed = analysis_data["pullback"].get("ready", False)
        rejection_confirmed = analysis_data["pullback"].get("rejection_candle", False)

    entry_mode = settings.entry_mode
    entry_price_source = "ASK" if direction == "BUY" else "BID"

    return {
        "symbol": symbol,
        "direction": direction,
        "entry_price": round(entry, 5),
        "stop_loss": round(stop_loss, 5),
        "take_profit_1": round(tp1, 5),
        "take_profit_2": round(tp2, 5),
        "take_profit_3": round(tp3, 5),
        "risk_reward": round(rr_ratio, 2),
        "confidence": confidence,
        "risk_percent": settings.risk_per_trade_percent,
        "signal_id": signal_id,
        "manual_approval_required": settings.manual_approval_required,
        "entry_mode": entry_mode,
        "entry_price_source": entry_price_source,
        "atr_sl": round(atr_sl, 5),
        "swing_sl": round(swing_sl, 5),
        "final_sl": round(stop_loss, 5),
        "sl_distance": round(sl_distance, 5),
        "min_sl_distance": min_sl_distance,
        "fib_zone_low": round(fib_zone_low, 5),
        "fib_zone_high": round(fib_zone_high, 5),
        "pullback_confirmed": pullback_confirmed,
        "rejection_candle_confirmed": rejection_confirmed,
        "reason_json": {
            "atr": atr,
            "entry_type": entry_mode,
            "entry_price_source": entry_price_source,
            "sl_method": "min(ATR_SL, Swing_SL+buffer)" if direction == "BUY" else "max(ATR_SL, Swing_SL+buffer)",
            "atr_multiplier": settings.atr_sl_multiplier,
            "buffer_multiplier": settings.sl_atr_buffer_multiplier,
        },
    }
