from typing import Dict, List
from app.indicators import find_swing_high, find_swing_low


def calculate_fibonacci_levels(highs: List[float], lows: List[float], direction: str, lookback: int = 50) -> Dict:
    if len(highs) < lookback:
        return {"valid": False, "levels": {}, "zone_low": 0, "zone_high": 0}

    swing_high = find_swing_high(highs, lookback)
    swing_low = find_swing_low(lows, lookback)

    if swing_high <= swing_low:
        return {"valid": False, "levels": {}, "zone_low": 0, "zone_high": 0}

    diff = swing_high - swing_low

    if direction == "BUY":
        # Retracement from high to low (pullback down in uptrend)
        levels = {
            "0.0": swing_high,
            "0.236": swing_high - diff * 0.236,
            "0.382": swing_high - diff * 0.382,
            "0.5": swing_high - diff * 0.5,
            "0.618": swing_high - diff * 0.618,
            "0.786": swing_high - diff * 0.786,
            "1.0": swing_low,
        }
        zone_low = levels["0.618"]
        zone_high = levels["0.382"]
    else:
        # Retracement from low to high (pullback up in downtrend)
        levels = {
            "0.0": swing_low,
            "0.236": swing_low + diff * 0.236,
            "0.382": swing_low + diff * 0.382,
            "0.5": swing_low + diff * 0.5,
            "0.618": swing_low + diff * 0.618,
            "0.786": swing_low + diff * 0.786,
            "1.0": swing_high,
        }
        zone_low = levels["0.382"]
        zone_high = levels["0.618"]

    # Round all values
    levels = {k: round(v, 5) for k, v in levels.items()}

    return {
        "valid": True,
        "direction": direction,
        "swing_high": round(swing_high, 5),
        "swing_low": round(swing_low, 5),
        "levels": levels,
        "zone_low": round(zone_low, 5),
        "zone_high": round(zone_high, 5),
    }


def is_in_pullback_zone(price: float, fib_data: Dict) -> bool:
    if not fib_data.get("valid"):
        return False
    return fib_data["zone_low"] <= price <= fib_data["zone_high"]
