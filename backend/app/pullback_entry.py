from typing import Dict, Optional
from app.config import settings
from app.fibonacci import calculate_fibonacci_levels, is_in_pullback_zone
from app.indicators import detect_rejection_candle


def check_pullback_entry(direction: str, current_price: float, ema20_m5: float, atr: float, highs: list, lows: list, last_candle: dict, fib_data: Optional[Dict] = None) -> Dict:
    """Check if price has pulled back to a valid entry zone."""

    tolerance = settings.pullback_ema_tolerance_atr_ratio * atr
    near_ema20 = abs(current_price - ema20_m5) <= tolerance

    in_fib_zone = False
    if fib_data and fib_data.get("valid"):
        in_fib_zone = is_in_pullback_zone(current_price, fib_data)

    pullback_valid = near_ema20 or in_fib_zone

    # Check rejection candle
    rejection = False
    if settings.require_rejection_candle and last_candle:
        rejection = detect_rejection_candle(
            last_candle, direction, ema20_m5, settings.rejection_wick_body_ratio
        )
    elif not settings.require_rejection_candle:
        rejection = True

    ready = pullback_valid and rejection

    status = "NOT_READY"
    if ready:
        status = f"PULLBACK_{direction}_READY"
    elif pullback_valid and not rejection:
        status = "WAITING_REJECTION"
    elif not pullback_valid:
        status = "WAITING_PULLBACK"

    return {
        "pullback_valid": pullback_valid,
        "near_ema20": near_ema20,
        "in_fib_zone": in_fib_zone,
        "rejection_candle": rejection,
        "ready": ready,
        "status": status,
        "ema20_distance": round(abs(current_price - ema20_m5), 5),
        "tolerance": round(tolerance, 5),
    }
