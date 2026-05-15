from typing import Dict, List, Optional
from app.mt5_client import mt5_client
from app.indicators import calculate_ema, calculate_rsi, calculate_atr, calculate_adx, calculate_macd
from app.market_condition import classify_market_condition, classify_trend, is_trend_bullish, is_trend_bearish
from app.support_resistance import calculate_support_resistance
from app.fibonacci import calculate_fibonacci_levels
from app.config import settings


def get_closed_candles(symbol: str, timeframe: str, count: int = 100) -> List[Dict]:
    candles = mt5_client.get_candles(symbol, timeframe, count + 1)
    if len(candles) <= 1:
        return []
    return candles[:-1]


def analyze_timeframe(symbol: str, timeframe: str) -> Optional[Dict]:
    candles = get_closed_candles(symbol, timeframe, 100)
    if len(candles) < 50:
        return None

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    rsi14 = calculate_rsi(closes, 14)
    atr14 = calculate_atr(highs, lows, closes, 14)
    adx14 = calculate_adx(highs, lows, closes, settings.adx_period)
    macd = calculate_macd(closes, settings.macd_fast, settings.macd_slow, settings.macd_signal)

    # EMA distance
    ema_distance = abs(ema20 - ema50)
    ema_distance_atr_ratio = round(ema_distance / atr14, 4) if atr14 > 0 else 0

    # Trend classification
    last_close = closes[-1]
    trend = classify_trend(ema20, ema50, last_close, adx14, ema_distance_atr_ratio)

    # Market condition
    market_condition = classify_market_condition(adx14, atr14, ema_distance_atr_ratio)

    # Support/Resistance
    sr = calculate_support_resistance(
        highs, lows, closes, atr14,
        settings.sr_lookback_short, settings.sr_lookback_long
    )

    last_candle = candles[-1]

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend": trend,
        "ema20": ema20,
        "ema50": ema50,
        "rsi14": rsi14,
        "atr14": atr14,
        "adx14": adx14,
        "macd": macd,
        "ema_distance": round(ema_distance, 5),
        "ema_distance_atr_ratio": ema_distance_atr_ratio,
        "market_condition": market_condition,
        "support_resistance": sr,
        "last_close": last_candle["close"],
        "last_high": last_candle["high"],
        "last_low": last_candle["low"],
        "last_candle": last_candle,
        "candle_time": last_candle["time"],
        "candle_count": len(candles),
        "highs": highs,
        "lows": lows,
    }


def multi_timeframe_analysis(symbol: str) -> Optional[Dict]:
    h1 = analyze_timeframe(symbol, "H1")
    m30 = analyze_timeframe(symbol, "M30")
    m15 = analyze_timeframe(symbol, "M15")
    m5 = analyze_timeframe(symbol, "M5")

    if not h1 or not m30 or not m15 or not m5:
        return None

    all_bullish = (
        is_trend_bullish(h1["trend"])
        and is_trend_bullish(m30["trend"])
        and is_trend_bullish(m15["trend"])
        and is_trend_bullish(m5["trend"])
    )
    all_bearish = (
        is_trend_bearish(h1["trend"])
        and is_trend_bearish(m30["trend"])
        and is_trend_bearish(m15["trend"])
        and is_trend_bearish(m5["trend"])
    )

    if all_bullish:
        market_condition = "TRENDING_UP"
    elif all_bearish:
        market_condition = "TRENDING_DOWN"
    else:
        market_condition = "MIXED"

    # Fibonacci
    direction = "BUY" if all_bullish else "SELL" if all_bearish else None
    fib_data = {"valid": False, "levels": {}, "zone_low": 0, "zone_high": 0}
    if direction:
        fib_data = calculate_fibonacci_levels(
            m5["highs"], m5["lows"], direction, settings.fib_lookback
        )

    return {
        "symbol": symbol,
        "h1": h1,
        "m30": m30,
        "m15": m15,
        "m5": m5,
        "market_condition": market_condition,
        "fibonacci": fib_data,
    }


def evaluate_signal_candidate(analysis: Dict, spread: float, max_spread: float) -> Dict:
    h1 = analysis["h1"]
    m30 = analysis["m30"]
    m15 = analysis["m15"]
    m5 = analysis["m5"]

    reasons = []
    direction = None
    status = "WAIT"

    spread_ok = spread <= max_spread
    if not spread_ok:
        reasons.append(f"Spread too high: {spread} > {max_spread}")
        return {"status": "WAIT", "direction": None, "reasons": reasons, "confidence": 0}

    all_bullish = (
        is_trend_bullish(h1["trend"])
        and is_trend_bullish(m30["trend"])
        and is_trend_bullish(m15["trend"])
        and is_trend_bullish(m5["trend"])
    )
    all_bearish = (
        is_trend_bearish(h1["trend"])
        and is_trend_bearish(m30["trend"])
        and is_trend_bearish(m15["trend"])
        and is_trend_bearish(m5["trend"])
    )

    # BUY candidate check
    if all_bullish:
        rsi_ok = 50 <= m5["rsi14"] <= 70
        close_above_ema = m5["last_close"] > m5["ema20"]

        if rsi_ok and close_above_ema:
            direction = "BUY"
            status = "WATCH_BUY"
            reasons.append(f"H1 trend {h1['trend']}")
            reasons.append(f"M30 trend {m30['trend']}")
            reasons.append(f"M15 trend {m15['trend']}")
            reasons.append(f"M5 trend {m5['trend']}")
            reasons.append(f"M5 RSI {m5['rsi14']:.1f} in healthy range (50-70)")
            reasons.append("M5 close above EMA20")
            reasons.append(f"Spread {spread} within limit")
        elif not rsi_ok:
            reasons.append(f"M5 RSI {m5['rsi14']:.1f} outside 50-70 range")
        elif not close_above_ema:
            reasons.append("M5 close not above EMA20")

    # SELL candidate check
    elif all_bearish:
        rsi_ok = 30 <= m5["rsi14"] <= 50
        close_below_ema = m5["last_close"] < m5["ema20"]

        if rsi_ok and close_below_ema:
            direction = "SELL"
            status = "WATCH_SELL"
            reasons.append(f"H1 trend {h1['trend']}")
            reasons.append(f"M30 trend {m30['trend']}")
            reasons.append(f"M15 trend {m15['trend']}")
            reasons.append(f"M5 trend {m5['trend']}")
            reasons.append(f"M5 RSI {m5['rsi14']:.1f} in healthy range (30-50)")
            reasons.append("M5 close below EMA20")
            reasons.append(f"Spread {spread} within limit")
        elif not rsi_ok:
            reasons.append(f"M5 RSI {m5['rsi14']:.1f} outside 30-50 range")
        elif not close_below_ema:
            reasons.append("M5 close not below EMA20")

    else:
        reasons.append(f"Mixed timeframes: H1={h1['trend']}, M30={m30['trend']}, M15={m15['trend']}, M5={m5['trend']}")

    if not reasons:
        reasons.append("No clear setup")

    # Calculate confidence
    confidence = calculate_confidence(analysis, spread, max_spread, direction)

    return {
        "status": status,
        "direction": direction,
        "reasons": reasons,
        "confidence": confidence,
    }


def calculate_confidence(analysis: Dict, spread: float, max_spread: float, direction: Optional[str]) -> int:
    if direction is None:
        return 0

    score = 0
    h1 = analysis["h1"]
    m30 = analysis["m30"]
    m15 = analysis["m15"]
    m5 = analysis["m5"]

    # H1 strong trend alignment: 12 points
    if direction == "BUY" and h1["trend"] == "BULLISH_STRONG":
        score += 12
    elif direction == "SELL" and h1["trend"] == "BEARISH_STRONG":
        score += 12
    elif (direction == "BUY" and is_trend_bullish(h1["trend"])) or (direction == "SELL" and is_trend_bearish(h1["trend"])):
        score += 7

    # M30 strong trend alignment: 12 points
    if direction == "BUY" and m30["trend"] == "BULLISH_STRONG":
        score += 12
    elif direction == "SELL" and m30["trend"] == "BEARISH_STRONG":
        score += 12
    elif (direction == "BUY" and is_trend_bullish(m30["trend"])) or (direction == "SELL" and is_trend_bearish(m30["trend"])):
        score += 7

    # M15 strong trend alignment: 12 points
    if direction == "BUY" and m15["trend"] == "BULLISH_STRONG":
        score += 12
    elif direction == "SELL" and m15["trend"] == "BEARISH_STRONG":
        score += 12
    elif (direction == "BUY" and is_trend_bullish(m15["trend"])) or (direction == "SELL" and is_trend_bearish(m15["trend"])):
        score += 7

    # M5 strong trend alignment: 10 points
    if direction == "BUY" and m5["trend"] == "BULLISH_STRONG":
        score += 10
    elif direction == "SELL" and m5["trend"] == "BEARISH_STRONG":
        score += 10
    elif (direction == "BUY" and is_trend_bullish(m5["trend"])) or (direction == "SELL" and is_trend_bearish(m5["trend"])):
        score += 5

    # ADX trend condition: 10 points
    adx = m5.get("adx14", 0)
    if adx >= settings.adx_strong_trend:
        score += 10
    elif adx >= settings.adx_min_trend:
        score += 5

    # EMA distance healthy: 10 points
    ema_ratio = m5.get("ema_distance_atr_ratio", 0)
    if ema_ratio >= settings.min_ema_distance_atr_ratio:
        score += 10

    # RSI healthy: 10 points
    if direction == "BUY" and 50 <= m5["rsi14"] <= 70:
        score += 10
    elif direction == "SELL" and 30 <= m5["rsi14"] <= 50:
        score += 10

    # MACD confirmation: 10 points
    macd = m5.get("macd", {})
    if direction == "BUY" and macd.get("histogram", 0) > 0:
        score += 10
    elif direction == "SELL" and macd.get("histogram", 0) < 0:
        score += 10

    # Spread normal: 5 points
    if spread <= max_spread * 0.7:
        score += 5
    elif spread <= max_spread:
        score += 3

    # Pullback zone: 5 points (added later when pullback is checked)
    # Rejection candle: 5 points (added later)

    # Caps
    if adx < settings.adx_min_trend:
        score = min(score, 60)
    if macd.get("histogram", 0) != 0:
        macd_against = (direction == "BUY" and macd["histogram"] < 0) or (direction == "SELL" and macd["histogram"] > 0)
        if macd_against:
            score = min(score, 70)

    return min(score, 100)
