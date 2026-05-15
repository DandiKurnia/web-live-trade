from typing import List, Dict, Tuple
import numpy as np


def calculate_ema(prices: List[float], period: int) -> float:
    if len(prices) < period:
        return 0.0
    arr = np.array(prices, dtype=float)
    multiplier = 2 / (period + 1)
    ema = arr[0]
    for price in arr[1:]:
        ema = (price - ema) * multiplier + ema
    return round(float(ema), 5)


def calculate_ema_series(prices: List[float], period: int) -> List[float]:
    if len(prices) < period:
        return []
    arr = np.array(prices, dtype=float)
    multiplier = 2 / (period + 1)
    ema_values = [float(arr[0])]
    ema = arr[0]
    for price in arr[1:]:
        ema = (price - ema) * multiplier + ema
        ema_values.append(float(ema))
    return ema_values


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0
    arr = np.array(prices, dtype=float)
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 2)


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(highs) < period + 1:
        return 0.0
    true_ranges = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)
    if len(true_ranges) < period:
        return 0.0
    atr = np.mean(true_ranges[:period])
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
    return round(float(atr), 5)


def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(highs) < period * 2 + 1:
        return 0.0

    plus_dm = []
    minus_dm = []
    tr_list = []

    for i in range(1, len(highs)):
        high_diff = highs[i] - highs[i - 1]
        low_diff = lows[i - 1] - lows[i]

        pdm = high_diff if high_diff > low_diff and high_diff > 0 else 0
        mdm = low_diff if low_diff > high_diff and low_diff > 0 else 0
        plus_dm.append(pdm)
        minus_dm.append(mdm)

        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        tr_list.append(tr)

    if len(tr_list) < period:
        return 0.0

    # Smoothed values
    atr_smooth = sum(tr_list[:period])
    plus_smooth = sum(plus_dm[:period])
    minus_smooth = sum(minus_dm[:period])

    dx_values = []

    for i in range(period, len(tr_list)):
        atr_smooth = atr_smooth - (atr_smooth / period) + tr_list[i]
        plus_smooth = plus_smooth - (plus_smooth / period) + plus_dm[i]
        minus_smooth = minus_smooth - (minus_smooth / period) + minus_dm[i]

        if atr_smooth == 0:
            continue

        plus_di = 100 * plus_smooth / atr_smooth
        minus_di = 100 * minus_smooth / atr_smooth

        di_sum = plus_di + minus_di
        if di_sum == 0:
            dx_values.append(0)
        else:
            dx = 100 * abs(plus_di - minus_di) / di_sum
            dx_values.append(dx)

    if len(dx_values) < period:
        return 0.0

    adx = np.mean(dx_values[:period])
    for i in range(period, len(dx_values)):
        adx = (adx * (period - 1) + dx_values[i]) / period

    return round(float(adx), 2)


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    if len(prices) < slow + signal:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}

    fast_ema = calculate_ema_series(prices, fast)
    slow_ema = calculate_ema_series(prices, slow)

    # MACD line = fast EMA - slow EMA (aligned from slow start)
    macd_line_series = []
    offset = len(fast_ema) - len(slow_ema)
    for i in range(len(slow_ema)):
        macd_line_series.append(fast_ema[i + offset] - slow_ema[i])

    if len(macd_line_series) < signal:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}

    # Signal line = EMA of MACD line
    signal_ema = calculate_ema_series(macd_line_series, signal)

    macd_val = macd_line_series[-1]
    signal_val = signal_ema[-1] if signal_ema else 0.0
    histogram = macd_val - signal_val

    return {
        "macd_line": round(macd_val, 5),
        "signal_line": round(signal_val, 5),
        "histogram": round(histogram, 5),
    }


def find_swing_high(highs: List[float], lookback: int = 20) -> float:
    if len(highs) < lookback:
        return 0.0
    return max(highs[-lookback:])


def find_swing_low(lows: List[float], lookback: int = 20) -> float:
    if len(lows) < lookback:
        return 0.0
    return min(lows[-lookback:])


def detect_rejection_candle(candle: Dict, direction: str, ema20: float, wick_ratio: float = 1.5) -> bool:
    o = candle["open"]
    h = candle["high"]
    l = candle["low"]
    c = candle["close"]
    body = abs(c - o)
    if body == 0:
        body = 0.00001

    if direction == "BUY":
        lower_wick = min(o, c) - l
        if lower_wick >= body * wick_ratio and c > o and c >= ema20:
            return True
    elif direction == "SELL":
        upper_wick = h - max(o, c)
        if upper_wick >= body * wick_ratio and c < o and c <= ema20:
            return True

    return False
