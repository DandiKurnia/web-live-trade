from typing import Dict
from app.indicators import calculate_ema, calculate_rsi


def generate_signal(close_prices: list, bid: float, ask: float, symbol: str, timeframe: str = "M5") -> Dict:
    ema20 = calculate_ema(close_prices, 20)
    ema50 = calculate_ema(close_prices, 50)
    rsi = calculate_rsi(close_prices, 14)
    spread = round(ask - bid, 5)

    if ema20 == 0 or ema50 == 0:
        signal = "WAIT"
        reason = "Not enough data to calculate indicators"
    elif ema20 > ema50 and rsi > 50:
        signal = "BUY"
        reason = f"EMA20 ({ema20}) > EMA50 ({ema50}) and RSI ({rsi}) > 50"
    elif ema20 < ema50 and rsi < 50:
        signal = "SELL"
        reason = f"EMA20 ({ema20}) < EMA50 ({ema50}) and RSI ({rsi}) < 50"
    else:
        signal = "WAIT"
        reason = f"Mixed signals: EMA20={ema20}, EMA50={ema50}, RSI={rsi}"

    return {
        "symbol": symbol,
        "signal": signal,
        "reason": reason,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": rsi,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "timeframe": timeframe,
    }
