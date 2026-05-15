from fastapi import APIRouter, HTTPException
from app.mt5_client import mt5_client
from app.config import settings

router = APIRouter(prefix="/api")


def find_symbol(symbol: str) -> str:
    for s in settings.symbol_list:
        if s.lower() == symbol.lower():
            return s
    return ""


@router.get("/price/{symbol}")
async def get_price(symbol: str):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")
    tick = mt5_client.get_tick(matched)
    if tick is None:
        raise HTTPException(status_code=503, detail=f"No tick data for {matched}. MT5 may not be connected or market is closed.")
    return {"success": True, **tick}


@router.get("/symbols")
async def get_symbols():
    return {"symbols": settings.symbol_list}


@router.get("/candles/{symbol}")
async def get_candles(symbol: str, timeframe: str = "M1", limit: int = 100):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")
    if limit > 1000:
        limit = 1000
    candles = mt5_client.get_candles(matched, timeframe, limit)
    if not candles:
        raise HTTPException(status_code=503, detail=f"No candle data for {matched}")
    return {"symbol": matched, "timeframe": timeframe, "count": len(candles), "candles": candles}
