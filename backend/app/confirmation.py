from typing import Dict, List, Optional
from collections import deque

# Store last N signal candidates per symbol for confirmation
_candidate_history: Dict[str, deque] = {}


def get_history(symbol: str) -> deque:
    if symbol not in _candidate_history:
        _candidate_history[symbol] = deque(maxlen=10)
    return _candidate_history[symbol]


def record_candidate(symbol: str, candidate: Dict):
    history = get_history(symbol)
    history.append(candidate)


def check_confirmation(symbol: str, current_candidate: Dict, analysis: Dict) -> Dict:
    """
    Confirmation rules:
    - Technical candidate must appear on at least 2 of the last 3 closed M5 candles
    - H1 and M15 direction must still agree
    - Spread must still be valid
    """
    history = get_history(symbol)
    direction = current_candidate.get("direction")
    status = current_candidate.get("status")

    if not direction or status == "WAIT":
        return {
            "confirmed": False,
            "status": status or "WAIT",
            "reason": "No active candidate to confirm",
        }

    # Check last 3 entries for same direction
    recent = list(history)[-3:]
    if len(recent) < 2:
        return {
            "confirmed": False,
            "status": status,
            "reason": f"Need at least 2 candles with same direction, have {len(recent)}",
        }

    same_direction_count = sum(
        1 for r in recent
        if r.get("direction") == direction and r.get("status") != "WAIT"
    )

    if same_direction_count < 2:
        return {
            "confirmed": False,
            "status": status,
            "reason": f"Only {same_direction_count}/2 candles confirm {direction}",
        }

    # Verify H1, M30, and M15 still agree
    h1_trend = analysis["h1"]["trend"]
    m30_trend = analysis["m30"]["trend"]
    m15_trend = analysis["m15"]["trend"]

    expected_trend = "BULLISH" if direction == "BUY" else "BEARISH"

    if h1_trend != expected_trend:
        return {
            "confirmed": False,
            "status": status,
            "reason": f"H1 trend changed to {h1_trend}, expected {expected_trend}",
        }

    if m30_trend != expected_trend:
        return {
            "confirmed": False,
            "status": status,
            "reason": f"M30 trend changed to {m30_trend}, expected {expected_trend}",
        }

    if m15_trend != expected_trend:
        return {
            "confirmed": False,
            "status": status,
            "reason": f"M15 trend changed to {m15_trend}, expected {expected_trend}",
        }

    # Confirmed
    confirmed_status = "BUY_CONFIRMED" if direction == "BUY" else "SELL_CONFIRMED"
    return {
        "confirmed": True,
        "status": confirmed_status,
        "reason": f"{direction} confirmed: {same_direction_count}/3 candles agree, H1+M30+M15 aligned",
    }


def reset_history(symbol: str):
    if symbol in _candidate_history:
        _candidate_history[symbol].clear()
