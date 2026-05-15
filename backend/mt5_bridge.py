"""
MT5 Bridge Service
Runs on Windows PC alongside MetaTrader 5 terminal.
Exposes MT5 data via HTTP so the backend on Ubuntu can fetch it.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import uvicorn

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

WIB = timezone(timedelta(hours=7))

app = FastAPI(title="MT5 Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MT5_LOGIN = 0
MT5_PASSWORD = ""
MT5_SERVER = "JustMarkets-Demo2"

SYMBOLS = ["XAUUSD.m", "EURUSD.m", "GBPUSD.m", "BTCUSD.m"]

TF_MAP = {}
if MT5_AVAILABLE:
    TF_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }

_initialized = False


def ensure_connected():
    global _initialized, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
    if not MT5_AVAILABLE:
        return False
    if _initialized:
        return True
    if not mt5.initialize():
        return False
    if MT5_LOGIN:
        authorized = mt5.login(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
        if not authorized:
            mt5.shutdown()
            return False
    _initialized = True
    return True


@app.get("/health")
def health():
    connected = ensure_connected()
    return {"status": "ok", "mt5_connected": connected}


@app.get("/tick/{symbol}")
def get_tick(symbol: str):
    if not ensure_connected():
        raise HTTPException(status_code=503, detail="MT5 not connected")

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise HTTPException(status_code=404, detail=f"No tick for {symbol}")

    return {
        "symbol": symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "spread": round(tick.ask - tick.bid, 5),
        "time": datetime.fromtimestamp(tick.time, tz=WIB).isoformat(),
    }


@app.get("/candles/{symbol}")
def get_candles(symbol: str, timeframe: str = "M5", limit: int = 100):
    if not ensure_connected():
        raise HTTPException(status_code=503, detail="MT5 not connected")

    tf = TF_MAP.get(timeframe)
    if tf is None:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe: {timeframe}")

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, limit)
    if rates is None or len(rates) == 0:
        raise HTTPException(status_code=404, detail=f"No candles for {symbol} {timeframe}")

    candles = []
    for r in rates:
        candles.append({
            "time": datetime.fromtimestamp(r["time"], tz=WIB).isoformat(),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": int(r["tick_volume"]),
        })
    return candles


@app.get("/symbols")
def get_symbols():
    if not ensure_connected():
        raise HTTPException(status_code=503, detail="MT5 not connected")

    symbols = mt5.symbols_get()
    if symbols is None:
        return []
    return [s.name for s in symbols]


if __name__ == "__main__":
    import sys
    import os

    # Load from env or command line
    MT5_LOGIN = int(os.environ.get("MT5_LOGIN", "0"))
    MT5_PASSWORD = os.environ.get("MT5_PASSWORD", "")
    MT5_SERVER = os.environ.get("MT5_SERVER", "JustMarkets-Demo2")

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    print(f"Starting MT5 Bridge on port {port}...")
    print(f"MT5 Login: {MT5_LOGIN}, Server: {MT5_SERVER}")
    uvicorn.run(app, host="0.0.0.0", port=port)
