from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.config import settings
from app.database import async_session
from app.models import TradePlan, Signal, AIMarketSummary
from sqlalchemy import select

router = APIRouter(prefix="/api")


def find_symbol(symbol: str) -> str:
    for s in settings.symbol_list:
        if s.lower() == symbol.lower():
            return s
    return ""


@router.get("/trade-plans/{symbol}")
async def get_trade_plan(symbol: str):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")

    async with async_session() as session:
        result = await session.execute(
            select(TradePlan)
            .where(TradePlan.symbol == matched)
            .order_by(TradePlan.created_at.desc())
            .limit(1)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            return {"symbol": matched, "status": "NO_PLAN", "message": "No trade plan available"}

        return format_plan(plan)


@router.get("/trade-history")
async def get_trade_history(limit: int = 20):
    """Get all trade plans (approved, closed, rejected) as history."""
    async with async_session() as session:
        result = await session.execute(
            select(TradePlan)
            .where(TradePlan.status.in_(["APPROVED", "CLOSED", "REJECTED"]))
            .order_by(TradePlan.created_at.desc())
            .limit(limit)
        )
        plans = result.scalars().all()
        return {"trades": [format_plan(p) for p in plans]}


@router.get("/signal-history")
async def get_signal_history(limit: int = 30):
    """Get recent signal status changes and resolved AI alerts."""
    async with async_session() as session:
        # Get signal history
        result = await session.execute(
            select(Signal)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        signals = result.scalars().all()

        # Get resolved AI alerts
        result = await session.execute(
            select(AIMarketSummary)
            .where(AIMarketSummary.status.in_(["SL_HIT", "TP1_HIT", "TP2_HIT"]))
            .order_by(AIMarketSummary.resolved_at.desc())
            .limit(limit)
        )
        resolved_alerts = result.scalars().all()

        return {
            "signals": [format_signal(s) for s in signals],
            "resolved_alerts": [
                {
                    "id": a.id,
                    "symbol": a.symbol,
                    "direction": a.direction,
                    "status": a.status,
                    "entry_price": a.entry_price,
                    "exit_price": a.exit_price,
                    "stop_loss": a.stop_loss,
                    "take_profit_1": a.take_profit_1,
                    "take_profit_2": a.take_profit_2,
                    "risk_reward": a.risk_reward,
                    "ai_confidence": a.ai_confidence,
                    "profit_loss": a.profit_loss,
                    "exit_reason": a.exit_reason,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                }
                for a in resolved_alerts
            ],
        }


def format_plan(plan: TradePlan) -> dict:
    return {
        "id": plan.id,
        "symbol": plan.symbol,
        "direction": plan.direction,
        "status": plan.status,
        "entry_price": plan.entry_price,
        "stop_loss": plan.stop_loss,
        "take_profit_1": plan.take_profit_1,
        "take_profit_2": plan.take_profit_2,
        "take_profit_3": plan.take_profit_3,
        "risk_reward": plan.risk_reward,
        "confidence": plan.confidence,
        "risk_percent": plan.risk_percent,
        "entry_mode": plan.entry_mode,
        "entry_price_source": plan.entry_price_source,
        "sl_distance": plan.sl_distance,
        "manual_approval_required": plan.manual_approval_required,
        "approved_at": plan.approved_at.isoformat() if plan.approved_at else None,
        "rejected_at": plan.rejected_at.isoformat() if plan.rejected_at else None,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


def format_signal(s: Signal) -> dict:
    return {
        "id": s.id,
        "symbol": s.symbol,
        "status": s.status,
        "direction": s.direction,
        "confidence": s.confidence,
        "h1_trend": s.h1_trend,
        "m15_trend": s.m15_trend,
        "m5_trend": s.m5_trend,
        "market_condition": s.market_condition,
        "rsi14": s.rsi14,
        "adx14": s.adx14,
        "macd_histogram": s.macd_histogram,
        "spread": s.spread,
        "pullback_status": s.pullback_status,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.post("/trade-plans/{plan_id}/approve")
async def approve_trade_plan(plan_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(TradePlan).where(TradePlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Trade plan not found")
        if plan.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Cannot approve plan with status {plan.status}")

        plan.status = "APPROVED"
        plan.approved_at = datetime.utcnow()
        await session.commit()

        return {"id": plan.id, "status": "APPROVED", "message": "Trade plan approved. No order executed (manual mode)."}


@router.post("/trade-plans/{plan_id}/reject")
async def reject_trade_plan(plan_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(TradePlan).where(TradePlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Trade plan not found")
        if plan.status not in ("PENDING", "APPROVED"):
            raise HTTPException(status_code=400, detail=f"Cannot reject plan with status {plan.status}")

        plan.status = "REJECTED"
        plan.rejected_at = datetime.utcnow()
        await session.commit()

        return {"id": plan.id, "status": "REJECTED", "message": "Trade plan rejected."}
