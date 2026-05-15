from typing import Dict, List
from app.indicators import find_swing_high, find_swing_low


def calculate_support_resistance(highs: List[float], lows: List[float], closes: List[float], atr: float, short_lookback: int = 20, long_lookback: int = 50) -> Dict:
    swing_high_short = find_swing_high(highs, short_lookback)
    swing_low_short = find_swing_low(lows, short_lookback)
    swing_high_long = find_swing_high(highs, long_lookback)
    swing_low_long = find_swing_low(lows, long_lookback)

    current_price = closes[-1] if closes else 0

    nearest_resistance = min(swing_high_short, swing_high_long) if swing_high_short > 0 and swing_high_long > 0 else max(swing_high_short, swing_high_long)
    nearest_support = max(swing_low_short, swing_low_long) if swing_low_short > 0 and swing_low_long > 0 else min(swing_low_short, swing_low_long)

    # Use the closer resistance/support
    if swing_high_short > current_price:
        nearest_resistance = swing_high_short
    if swing_high_long > current_price and swing_high_long < nearest_resistance:
        nearest_resistance = swing_high_long

    if swing_low_short < current_price and swing_low_short > 0:
        nearest_support = swing_low_short
    if swing_low_long < current_price and swing_low_long > nearest_support:
        nearest_support = swing_low_long

    distance_to_resistance = nearest_resistance - current_price if nearest_resistance > current_price else 0
    distance_to_support = current_price - nearest_support if nearest_support < current_price and nearest_support > 0 else 0

    distance_to_resistance_atr = distance_to_resistance / atr if atr > 0 else 0
    distance_to_support_atr = distance_to_support / atr if atr > 0 else 0

    return {
        "swing_high_short": round(swing_high_short, 5),
        "swing_low_short": round(swing_low_short, 5),
        "swing_high_long": round(swing_high_long, 5),
        "swing_low_long": round(swing_low_long, 5),
        "nearest_resistance": round(nearest_resistance, 5),
        "nearest_support": round(nearest_support, 5),
        "distance_to_resistance": round(distance_to_resistance, 5),
        "distance_to_support": round(distance_to_support, 5),
        "distance_to_resistance_atr": round(distance_to_resistance_atr, 2),
        "distance_to_support_atr": round(distance_to_support_atr, 2),
    }
