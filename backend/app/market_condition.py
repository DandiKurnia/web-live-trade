from typing import Dict
from app.config import settings


def classify_market_condition(adx: float, atr: float, ema_distance_atr_ratio: float) -> str:
    if adx >= settings.adx_strong_trend and ema_distance_atr_ratio >= settings.min_ema_distance_atr_ratio:
        return "TRENDING_STRONG"
    elif adx >= settings.adx_min_trend:
        return "TRENDING"
    elif adx < settings.adx_min_trend:
        return "RANGING"
    return "NEUTRAL"


def classify_trend(ema20: float, ema50: float, close: float, adx: float, ema_distance_atr_ratio: float) -> str:
    if ema20 == 0 or ema50 == 0:
        return "NEUTRAL"

    is_bullish = ema20 > ema50
    is_bearish = ema20 < ema50
    strong_adx = adx >= settings.adx_strong_trend
    healthy_distance = ema_distance_atr_ratio >= settings.min_ema_distance_atr_ratio

    if is_bullish and strong_adx and healthy_distance and close > ema20:
        return "BULLISH_STRONG"
    elif is_bullish:
        return "BULLISH_WEAK"
    elif is_bearish and strong_adx and healthy_distance and close < ema20:
        return "BEARISH_STRONG"
    elif is_bearish:
        return "BEARISH_WEAK"

    if adx < settings.adx_min_trend:
        return "RANGING"

    return "NEUTRAL"


def is_trend_strong(trend: str) -> bool:
    return trend in ("BULLISH_STRONG", "BEARISH_STRONG")


def is_trend_bullish(trend: str) -> bool:
    return trend in ("BULLISH_STRONG", "BULLISH_WEAK")


def is_trend_bearish(trend: str) -> bool:
    return trend in ("BEARISH_STRONG", "BEARISH_WEAK")
