from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.mt5_client import mt5_client
from app.multi_timeframe_analysis import multi_timeframe_analysis, evaluate_signal_candidate
from app.ai_analysis import run_ai_analysis
from app.ai_client import ai_client
from app.database import async_session
from app.models import AIMarketSummary, AISchedulerRun
from app.telegram_bot import telegram_bot
from sqlalchemy import select, update

router = APIRouter(prefix="/api")

WIB = timezone(timedelta(hours=7))

# Cooldown tracking per symbol
_last_manual_trigger: dict = {}


def find_symbol(symbol: str) -> str:
    for s in settings.symbol_list:
        if s.lower() == symbol.lower():
            return s
    return ""


def now_naive():
    """Return current time as naive datetime (for DB storage)."""
    return datetime.utcnow()


def now_wib():
    """Return current time in WIB for display/cooldown logic."""
    return datetime.now(tz=WIB)


def get_next_auto_run() -> str:
    now = datetime.now(tz=WIB)
    allowed = settings.allowed_minutes_list
    for minute in sorted(allowed):
        candidate = now.replace(minute=minute, second=0, microsecond=0)
        if candidate > now:
            return candidate.isoformat()
    # Next hour, first allowed minute
    next_hour = (now + timedelta(hours=1)).replace(minute=allowed[0], second=0, microsecond=0)
    return next_hour.isoformat()


@router.get("/ai/status")
async def get_ai_status():
    # Get last auto run
    async with async_session() as session:
        result = await session.execute(
            select(AISchedulerRun)
            .where(AISchedulerRun.run_type == "AUTO")
            .order_by(AISchedulerRun.created_at.desc())
            .limit(1)
        )
        last_run = result.scalar_one_or_none()

    return {
        "auto_enabled": settings.ai_analysis_auto_enabled,
        "timezone": settings.app_timezone,
        "allowed_minutes": settings.allowed_minutes_list,
        "last_auto_run_at": last_run.started_at.isoformat() if last_run and last_run.started_at else None,
        "next_auto_run_at": get_next_auto_run(),
        "manual_cooldown_seconds": settings.ai_manual_trigger_cooldown_seconds,
        "ai_available": ai_client.is_available,
    }


@router.get("/ai/summary/{symbol}")
async def get_ai_summary(symbol: str):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")

    async with async_session() as session:
        # First try to find an active alert
        result = await session.execute(
            select(AIMarketSummary)
            .where(AIMarketSummary.symbol == matched, AIMarketSummary.status == "ACTIVE")
            .order_by(AIMarketSummary.created_at.desc())
            .limit(1)
        )
        summary = result.scalar_one_or_none()

        # Fall back to latest summary
        if not summary:
            result = await session.execute(
                select(AIMarketSummary)
                .where(AIMarketSummary.symbol == matched)
                .order_by(AIMarketSummary.created_at.desc())
                .limit(1)
            )
            summary = result.scalar_one_or_none()

        if not summary:
            return {
                "success": False,
                "symbol": matched,
                "ai_available": ai_client.is_available,
                "message": "No AI summary available yet",
            }

        return {
            "success": True,
            "symbol": summary.symbol,
            "trigger_type": summary.trigger_type,
            "ai_bias": summary.ai_bias,
            "direction": summary.direction,
            "ai_confidence": summary.ai_confidence,
            "recommendation": summary.recommendation,
            "setup_quality": summary.setup_quality,
            "entry_price": summary.entry_price,
            "entry_price_source": summary.entry_price_source,
            "stop_loss": summary.stop_loss,
            "take_profit_1": summary.take_profit_1,
            "take_profit_2": summary.take_profit_2,
            "risk_reward": summary.risk_reward,
            "summary": summary.summary,
            "entry_reason": summary.entry_reason,
            "risk_warning": summary.risk_warning,
            "should_create_trade_plan": summary.should_create_trade_plan,
            "manual_approval_required": summary.manual_approval_required,
            "ai_available": ai_client.is_available,
            "status": summary.status,
            "exit_price": summary.exit_price,
            "exit_reason": summary.exit_reason,
            "resolved_at": summary.resolved_at.isoformat() if summary.resolved_at else None,
            "profit_loss": summary.profit_loss,
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
        }


@router.post("/ai/analyze/{symbol}")
async def trigger_ai_analysis(symbol: str):
    matched = find_symbol(symbol)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not configured")

    if not ai_client.is_available:
        raise HTTPException(status_code=503, detail="AI provider is unavailable")

    # Cooldown check
    now = now_wib()
    last_trigger = _last_manual_trigger.get(matched)
    if last_trigger:
        elapsed = (now - last_trigger).total_seconds()
        remaining = settings.ai_manual_trigger_cooldown_seconds - elapsed
        if remaining > 0:
            raise HTTPException(
                status_code=429,
                detail=f"Cooldown active. Try again in {int(remaining)} seconds."
            )

    _last_manual_trigger[matched] = now

    analysis = multi_timeframe_analysis(matched)
    if not analysis:
        raise HTTPException(status_code=503, detail=f"Not enough data for {matched}")

    tick = mt5_client.get_tick(matched)
    spread = tick["spread"] if tick else 0
    max_spread = settings.get_max_spread(matched)
    candidate = evaluate_signal_candidate(analysis, spread, max_spread)

    started_at = now_naive()
    result = await run_ai_analysis(matched, analysis, candidate, spread, tick, trigger_type="MANUAL")
    if not result:
        async with async_session() as session:
            run_log = AISchedulerRun(
                run_type="MANUAL",
                symbol=matched,
                started_at=started_at,
                finished_at=now_naive(),
                status="FAILED",
                message="AI analysis returned no result",
            )
            session.add(run_log)
            await session.commit()
        raise HTTPException(status_code=503, detail="AI analysis failed")

    # Determine alert status
    is_valid_setup = (
        result.get("recommendation") == "VALID_SETUP"
        and result.get("direction") in ("BUY", "SELL")
        and result.get("entry_price") is not None
        and result.get("stop_loss") is not None
    )
    alert_status = "ACTIVE" if is_valid_setup else "INACTIVE"

    # Save to database
    async with async_session() as session:
        # Expire previous active alerts for this symbol
        if alert_status == "ACTIVE":
            await session.execute(
                update(AIMarketSummary)
                .where(AIMarketSummary.symbol == matched, AIMarketSummary.status == "ACTIVE")
                .values(status="EXPIRED")
            )

        db_summary = AIMarketSummary(
            symbol=matched,
            trigger_type="MANUAL",
            ai_bias=result.get("ai_bias"),
            direction=result.get("direction"),
            ai_confidence=result.get("ai_confidence", 0),
            recommendation=result.get("recommendation"),
            setup_quality=result.get("setup_quality"),
            entry_price=result.get("entry_price"),
            entry_price_source=result.get("entry_price_source"),
            stop_loss=result.get("stop_loss"),
            take_profit_1=result.get("take_profit_1"),
            take_profit_2=result.get("take_profit_2"),
            risk_reward=result.get("risk_reward"),
            summary=result.get("summary"),
            entry_reason=result.get("entry_reason"),
            risk_warning=result.get("risk_warning"),
            should_create_trade_plan=result.get("should_create_trade_plan", False),
            manual_approval_required=result.get("manual_approval_required", True),
            raw_request_json=result.get("raw_request_json"),
            raw_response_json=result.get("raw_response_json"),
            status=alert_status,
        )
        session.add(db_summary)

        run_log = AISchedulerRun(
            run_type="MANUAL",
            symbol=matched,
            started_at=started_at,
            finished_at=now_naive(),
            status="SUCCESS",
            message=f"AI returned {result.get('recommendation')}",
        )
        session.add(run_log)
        await session.commit()

    # Send Telegram notification
    await telegram_bot.notify_ai_analysis(result)

    return result


@router.get("/ai/active-alerts")
async def get_active_alerts():
    async with async_session() as session:
        result = await session.execute(
            select(AIMarketSummary)
            .where(AIMarketSummary.status == "ACTIVE")
            .order_by(AIMarketSummary.created_at.desc())
        )
        alerts = result.scalars().all()
        return {
            "alerts": [
                {
                    "id": a.id,
                    "symbol": a.symbol,
                    "trigger_type": a.trigger_type,
                    "ai_bias": a.ai_bias,
                    "direction": a.direction,
                    "ai_confidence": a.ai_confidence,
                    "recommendation": a.recommendation,
                    "setup_quality": a.setup_quality,
                    "entry_price": a.entry_price,
                    "entry_price_source": a.entry_price_source,
                    "stop_loss": a.stop_loss,
                    "take_profit_1": a.take_profit_1,
                    "take_profit_2": a.take_profit_2,
                    "risk_reward": a.risk_reward,
                    "summary": a.summary,
                    "entry_reason": a.entry_reason,
                    "risk_warning": a.risk_warning,
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts
            ]
        }
