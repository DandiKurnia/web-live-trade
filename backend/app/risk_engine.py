from typing import Dict, List
from datetime import date
from app.config import settings
from app.database import async_session
from app.models import TradePlan, RiskEvent
from sqlalchemy import select, func


class RiskEngine:
    async def check_risk(self, symbol: str, direction: str, confidence: int, spread: float, risk_reward: float, analysis_data: Dict = None) -> Dict:
        """Run all risk filters. Returns pass/fail with reasons and warnings."""
        blocks = []
        warnings = []

        # Spread check
        max_spread = settings.get_max_spread(symbol)
        if spread > max_spread:
            blocks.append(f"Spread too high: {spread} > {max_spread}")

        # Confidence check
        if confidence < settings.min_confidence:
            blocks.append(f"Confidence {confidence} below minimum {settings.min_confidence}")

        # Risk reward check
        if risk_reward < settings.min_risk_reward:
            blocks.append(f"Risk/reward {risk_reward:.2f} below minimum {settings.min_risk_reward}")

        # Daily trade count
        daily_count = await self._get_daily_trade_count(symbol)
        if daily_count >= settings.max_trades_per_day:
            blocks.append(f"Max trades per day reached ({daily_count}/{settings.max_trades_per_day})")

        # Active trade for same symbol
        has_active = await self._has_active_trade(symbol)
        if has_active:
            blocks.append(f"Already have active trade for {symbol}")

        # ADX check
        if analysis_data:
            adx = analysis_data.get("adx", 0)
            if adx < settings.adx_min_trend:
                blocks.append(f"ADX {adx:.1f} below minimum {settings.adx_min_trend} (market ranging)")

            # EMA distance check
            ema_ratio = analysis_data.get("ema_distance_atr_ratio", 0)
            if ema_ratio < settings.min_ema_distance_atr_ratio:
                blocks.append(f"EMA distance ratio {ema_ratio:.2f} below minimum {settings.min_ema_distance_atr_ratio}")

            # Support/Resistance proximity
            sr = analysis_data.get("support_resistance", {})
            if direction == "BUY" and sr.get("distance_to_resistance_atr", 99) < settings.min_distance_to_sr_atr_ratio:
                blocks.append(f"Too close to resistance ({sr.get('distance_to_resistance_atr', 0):.2f} ATR)")

            if direction == "SELL" and sr.get("distance_to_support_atr", 99) < settings.min_distance_to_sr_atr_ratio:
                blocks.append(f"Too close to support ({sr.get('distance_to_support_atr', 0):.2f} ATR)")

            # Min SL distance
            sl_distance = analysis_data.get("sl_distance", 0)
            min_sl = settings.get_min_sl_distance(symbol)
            if sl_distance > 0 and sl_distance < min_sl:
                blocks.append(f"SL distance {sl_distance:.5f} below minimum {min_sl}")

            # Pullback check
            if settings.entry_mode == "PULLBACK":
                pullback = analysis_data.get("pullback", {})
                if not pullback.get("ready", False):
                    blocks.append(f"Pullback not ready: {pullback.get('status', 'UNKNOWN')}")

            # MACD warning (soft)
            macd = analysis_data.get("macd", {})
            if direction == "BUY" and macd.get("histogram", 0) < 0:
                warnings.append("MACD histogram is negative (bearish momentum)")
            elif direction == "SELL" and macd.get("histogram", 0) > 0:
                warnings.append("MACD histogram is positive (bullish momentum)")

        passed = len(blocks) == 0

        if not passed:
            await self._log_risk_event(symbol, "BLOCKED", blocks)

        return {
            "passed": passed,
            "blocks": blocks,
            "warnings": warnings,
            "daily_trades": daily_count,
            "max_trades": settings.max_trades_per_day,
        }

    async def _get_daily_trade_count(self, symbol: str) -> int:
        today = date.today()
        async with async_session() as session:
            result = await session.execute(
                select(func.count(TradePlan.id)).where(
                    TradePlan.symbol == symbol,
                    func.date(TradePlan.created_at) == today,
                )
            )
            return result.scalar() or 0

    async def _has_active_trade(self, symbol: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(TradePlan.id).where(
                    TradePlan.symbol == symbol,
                    TradePlan.status.in_(["PENDING", "APPROVED"]),
                ).limit(1)
            )
            return result.scalar() is not None

    async def _log_risk_event(self, symbol: str, event_type: str, blocks: List[str]):
        async with async_session() as session:
            event = RiskEvent(
                symbol=symbol,
                event_type=event_type,
                message="; ".join(blocks),
                details_json={"blocks": blocks},
            )
            session.add(event)
            await session.commit()


risk_engine = RiskEngine()
