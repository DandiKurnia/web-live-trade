from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from app.config import settings
import httpx
import logging

WIB = timezone(timedelta(hours=7))
logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class MT5Client:
    _initialized: bool = False

    @property
    def _use_bridge(self) -> bool:
        return bool(getattr(settings, "mt5_bridge_url", ""))

    def initialize(self) -> bool:
        if self._use_bridge:
            try:
                res = httpx.get(f"{settings.mt5_bridge_url}/health", timeout=5.0)
                if res.status_code == 200 and res.json().get("mt5_connected"):
                    self._initialized = True
                    return True
            except Exception as e:
                logger.warning(f"MT5 bridge health check failed: {e}")
            return False

        if not MT5_AVAILABLE:
            return False
        if self._initialized:
            return True
        if not mt5.initialize():
            return False
        authorized = mt5.login(
            login=settings.mt5_login,
            password=settings.mt5_password,
            server=settings.mt5_server,
        )
        if not authorized:
            mt5.shutdown()
            return False
        self._initialized = True
        return True

    def shutdown(self):
        if not self._use_bridge and self._initialized and MT5_AVAILABLE:
            mt5.shutdown()
            self._initialized = False

    @property
    def is_connected(self) -> bool:
        if self._use_bridge:
            try:
                res = httpx.get(f"{settings.mt5_bridge_url}/health", timeout=3.0)
                return res.status_code == 200 and res.json().get("mt5_connected", False)
            except Exception:
                return False

        if not MT5_AVAILABLE or not self._initialized:
            return False
        info = mt5.terminal_info()
        return info is not None and info.connected

    def get_tick(self, symbol: str) -> Optional[Dict]:
        if self._use_bridge:
            try:
                res = httpx.get(f"{settings.mt5_bridge_url}/tick/{symbol}", timeout=5.0)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                logger.warning(f"Bridge get_tick failed for {symbol}: {e}")
            return None

        if not self._initialized:
            return None
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": round(tick.ask - tick.bid, 5),
            "time": datetime.fromtimestamp(tick.time, tz=WIB).isoformat(),
        }

    def get_symbols(self) -> List[str]:
        if self._use_bridge:
            try:
                res = httpx.get(f"{settings.mt5_bridge_url}/symbols", timeout=5.0)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                logger.warning(f"Bridge get_symbols failed: {e}")
            return []

        if not self._initialized:
            return []
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        return [s.name for s in symbols]

    def get_candles(self, symbol: str, timeframe: str = "M1", limit: int = 100) -> List[Dict]:
        if self._use_bridge:
            try:
                res = httpx.get(
                    f"{settings.mt5_bridge_url}/candles/{symbol}",
                    params={"timeframe": timeframe, "limit": limit},
                    timeout=10.0,
                )
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                logger.warning(f"Bridge get_candles failed for {symbol} {timeframe}: {e}")
            return []

        if not self._initialized:
            return []
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_M1)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, limit)
        if rates is None or len(rates) == 0:
            return []
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


mt5_client = MT5Client()
