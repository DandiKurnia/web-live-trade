from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import asyncio
import logging
import json

from app.config import settings
from app.database import init_db, async_session
from app.mt5_client import mt5_client
from app.websocket_manager import ws_manager
from app.routes import health, market, signals, ai, trade_plans, agent
from app.models import MarketTick, Signal, TradePlan
from app.multi_timeframe_analysis import multi_timeframe_analysis, evaluate_signal_candidate
from app.confirmation import record_candidate, check_confirmation
from app.risk_engine import risk_engine
from app.trade_plan import generate_trade_plan
from app.ai_analysis import run_ai_analysis
from app.telegram_bot import telegram_bot
from app.pullback_entry import check_pullback_entry

logger = logging.getLogger(__name__)

# In-memory signal state
_signal_state: dict = {}
_last_m5_candle_time: dict = {}

# Signal WebSocket manager
signal_connections: list = []


async def tick_broadcast_loop():
    """Send live prices via WebSocket every 1 second."""
    while True:
        for symbol in settings.symbol_list:
            tick = mt5_client.get_tick(symbol)
            if tick:
                await ws_manager.broadcast(symbol, {
                    "type": "price_update",
                    **tick,
                })
        await asyncio.sleep(settings.live_price_interval_seconds)


async def tick_save_loop():
    """Save tick data to database every N seconds."""
    while True:
        async with async_session() as session:
            for symbol in settings.symbol_list:
                tick = mt5_client.get_tick(symbol)
                if tick:
                    market_tick = MarketTick(
                        symbol=symbol,
                        bid=tick["bid"],
                        ask=tick["ask"],
                        spread=tick["spread"],
                        source="mt5",
                    )
                    session.add(market_tick)
            await session.commit()
        await asyncio.sleep(settings.tick_save_interval_seconds)


async def signal_check_loop():
    """Check signals only when a new M5 candle closes."""
    global _signal_state, _last_m5_candle_time

    while True:
        for symbol in settings.symbol_list:
            try:
                analysis = multi_timeframe_analysis(symbol)
                if not analysis:
                    continue

                m5 = analysis["m5"]
                candle_time = m5["candle_time"]

                # Only process when a new candle closes
                if _last_m5_candle_time.get(symbol) == candle_time:
                    continue
                _last_m5_candle_time[symbol] = candle_time

                tick = mt5_client.get_tick(symbol)
                spread = tick["spread"] if tick else 0
                max_spread = settings.get_max_spread(symbol)

                # Evaluate candidate
                candidate = evaluate_signal_candidate(analysis, spread, max_spread)
                record_candidate(symbol, candidate)

                # Check confirmation
                confirmation = check_confirmation(symbol, candidate, analysis)

                status = confirmation["status"]
                direction = candidate.get("direction")
                confidence = candidate.get("confidence", 0)

                # Pullback check
                pullback = {"ready": False, "status": "NOT_CHECKED"}
                fib = analysis.get("fibonacci", {})
                if direction:
                    pullback = check_pullback_entry(
                        direction, m5["last_close"], m5["ema20"], m5["atr14"],
                        m5.get("highs", []), m5.get("lows", []),
                        m5.get("last_candle", {}), fib,
                    )

                prev_state = _signal_state.get(symbol, {})
                prev_status = prev_state.get("status")

                sr = m5.get("support_resistance", {})
                macd = m5.get("macd", {})

                # Build signal state
                signal_data = {
                    "symbol": symbol,
                    "status": status,
                    "direction": direction,
                    "confidence": confidence,
                    "reasons": candidate.get("reasons", []),
                    "h1_trend": analysis["h1"]["trend"],
                    "m30_trend": analysis["m30"]["trend"],
                    "m15_trend": analysis["m15"]["trend"],
                    "m5_trend": analysis["m5"]["trend"],
                    "market_condition": m5.get("market_condition", ""),
                    "rsi14": m5["rsi14"],
                    "atr14": m5["atr14"],
                    "adx14": m5.get("adx14", 0),
                    "macd_histogram": macd.get("histogram", 0),
                    "ema_distance_atr_ratio": m5.get("ema_distance_atr_ratio", 0),
                    "spread": spread,
                    "nearest_support": sr.get("nearest_support", 0),
                    "nearest_resistance": sr.get("nearest_resistance", 0),
                    "distance_to_support": sr.get("distance_to_support_atr", 0),
                    "distance_to_resistance": sr.get("distance_to_resistance_atr", 0),
                    "pullback_status": pullback.get("status", ""),
                    "rejection_candle_status": pullback.get("rejection_candle", False),
                    "timeframe": "M5",
                    "candle_time": candle_time,
                    "confirmation_reason": confirmation.get("reason", ""),
                }

                _signal_state[symbol] = signal_data

                # Import into signals route state
                from app.routes.signals import _signal_state as route_state
                route_state[symbol] = signal_data

                # Save to DB only when status changes
                if status != prev_status:
                    async with async_session() as session:
                        db_signal = Signal(
                            symbol=symbol,
                            status=status,
                            direction=direction,
                            timeframe="M5",
                            confidence=confidence,
                            reason_json=candidate.get("reasons", []),
                            h1_trend=analysis["h1"]["trend"],
                            m30_trend=analysis["m30"]["trend"],
                            m15_trend=analysis["m15"]["trend"],
                            m5_trend=analysis["m5"]["trend"],
                            market_condition=m5.get("market_condition", ""),
                            rsi14=m5["rsi14"],
                            atr14=m5["atr14"],
                            adx14=m5.get("adx14", 0),
                            macd_line=macd.get("macd_line", 0),
                            macd_signal_val=macd.get("signal_line", 0),
                            macd_histogram=macd.get("histogram", 0),
                            ema_distance_atr_ratio=m5.get("ema_distance_atr_ratio", 0),
                            spread=spread,
                            nearest_support=sr.get("nearest_support", 0),
                            nearest_resistance=sr.get("nearest_resistance", 0),
                            distance_to_support=sr.get("distance_to_support_atr", 0),
                            distance_to_resistance=sr.get("distance_to_resistance_atr", 0),
                            pullback_status=pullback.get("status", ""),
                            rejection_candle_status=pullback.get("rejection_candle", False),
                        )
                        session.add(db_signal)
                        await session.commit()
                        signal_id = db_signal.id

                    # Broadcast signal update
                    await broadcast_signal_update(signal_data)

                    # Telegram notification for important status changes
                    if status in ("WATCH_BUY", "WATCH_SELL", "BUY_CONFIRMED", "SELL_CONFIRMED"):
                        await telegram_bot.notify_signal_change(signal_data)

                    # If confirmed, try to create trade plan
                    if status in ("BUY_CONFIRMED", "SELL_CONFIRMED") and direction:
                        await handle_confirmed_signal(symbol, direction, confidence, signal_id, analysis, spread, pullback, fib)

            except Exception as e:
                logger.error(f"Signal check error for {symbol}: {e}")

        await asyncio.sleep(5)


async def handle_confirmed_signal(symbol: str, direction: str, confidence: int, signal_id: int, analysis: dict, spread: float, pullback: dict = None, fib: dict = None):
    """Handle confirmed signal: pullback check → risk check → trade plan."""
    tick = mt5_client.get_tick(symbol)
    if not tick:
        return

    m5 = analysis["m5"]
    sr = m5.get("support_resistance", {})
    macd = m5.get("macd", {})

    # Build analysis_data for risk engine
    analysis_data = {
        "adx": m5.get("adx14", 0),
        "ema_distance_atr_ratio": m5.get("ema_distance_atr_ratio", 0),
        "support_resistance": sr,
        "macd": macd,
        "pullback": pullback or {"ready": False, "status": "NOT_CHECKED"},
        "fibonacci": fib or {"valid": False},
    }

    # Generate trade plan preview
    plan = generate_trade_plan(symbol, direction, confidence, signal_id, analysis, analysis_data)
    if not plan:
        return

    # Add SL distance to analysis_data for risk check
    analysis_data["sl_distance"] = plan.get("sl_distance", 0)

    # Risk check
    risk_result = await risk_engine.check_risk(
        symbol, direction, confidence, spread, plan["risk_reward"], analysis_data
    )

    if not risk_result["passed"]:
        _signal_state[symbol]["status"] = "CANCELLED"
        _signal_state[symbol]["reasons"] = risk_result["blocks"]
        return

    # Save trade plan
    async with async_session() as session:
        db_plan = TradePlan(
            symbol=symbol,
            direction=direction,
            status="PENDING",
            entry_price=plan["entry_price"],
            stop_loss=plan["stop_loss"],
            take_profit_1=plan["take_profit_1"],
            take_profit_2=plan["take_profit_2"],
            take_profit_3=plan.get("take_profit_3"),
            risk_reward=plan["risk_reward"],
            confidence=confidence,
            risk_percent=plan["risk_percent"],
            signal_id=signal_id,
            manual_approval_required=plan["manual_approval_required"],
            entry_mode=plan.get("entry_mode"),
            entry_price_source=plan.get("entry_price_source"),
            atr_sl=plan.get("atr_sl"),
            swing_sl=plan.get("swing_sl"),
            final_sl=plan.get("final_sl"),
            sl_distance=plan.get("sl_distance"),
            min_sl_distance=plan.get("min_sl_distance"),
            fib_zone_low=plan.get("fib_zone_low"),
            fib_zone_high=plan.get("fib_zone_high"),
            pullback_confirmed=plan.get("pullback_confirmed"),
            rejection_candle_confirmed=plan.get("rejection_candle_confirmed"),
            reason_json=plan["reason_json"],
        )
        session.add(db_plan)
        await session.commit()

    # Update signal state
    plan_status = f"{direction}_PLAN_READY"
    _signal_state[symbol]["status"] = plan_status
    await broadcast_signal_update(_signal_state[symbol])

    # Telegram notification for trade plan ready
    await telegram_bot.notify_plan_ready(plan)


async def ai_analysis_loop():
    """Run AI analysis at wall-clock aligned times (e.g., :00 and :30)."""
    from app.models import AIMarketSummary, AISchedulerRun

    last_run_minute = None

    while True:
        now = datetime.now(tz=timezone(timedelta(hours=7)))
        current_minute = now.minute

        # Only run if current minute is in allowed list and hasn't run this minute
        if (settings.ai_analysis_auto_enabled
                and current_minute in settings.allowed_minutes_list
                and last_run_minute != current_minute):

            last_run_minute = current_minute
            logger.info(f"AI auto analysis triggered at {now.strftime('%H:%M')}")

            for symbol in settings.symbol_list:
                try:
                    analysis = multi_timeframe_analysis(symbol)
                    if not analysis:
                        continue

                    tick = mt5_client.get_tick(symbol)
                    spread = tick["spread"] if tick else 0
                    max_spread = settings.get_max_spread(symbol)
                    candidate = evaluate_signal_candidate(analysis, spread, max_spread)

                    started_at = datetime.utcnow()
                    result = await run_ai_analysis(symbol, analysis, candidate, spread, tick, trigger_type="AUTO")

                    async with async_session() as session:
                        if result:
                            is_valid_setup = (
                                result.get("recommendation") == "VALID_SETUP"
                                and result.get("direction") in ("BUY", "SELL")
                                and result.get("entry_price") is not None
                                and result.get("stop_loss") is not None
                            )
                            alert_status = "ACTIVE" if is_valid_setup else "INACTIVE"

                            # Expire previous active alerts for this symbol
                            if alert_status == "ACTIVE":
                                from sqlalchemy import update
                                await session.execute(
                                    update(AIMarketSummary)
                                    .where(AIMarketSummary.symbol == symbol, AIMarketSummary.status == "ACTIVE")
                                    .values(status="EXPIRED")
                                )

                            db_summary = AIMarketSummary(
                                symbol=symbol,
                                trigger_type="AUTO",
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
                                run_type="AUTO",
                                symbol=symbol,
                                scheduled_time=datetime.utcnow(),
                                started_at=started_at,
                                finished_at=datetime.utcnow(),
                                status="SUCCESS",
                                message=f"AI returned {result.get('recommendation')}",
                            )
                            session.add(run_log)

                            # Telegram notification for auto AI
                            await telegram_bot.notify_ai_analysis(result)
                        else:
                            run_log = AISchedulerRun(
                                run_type="AUTO",
                                symbol=symbol,
                                scheduled_time=datetime.utcnow(),
                                started_at=started_at,
                                finished_at=datetime.utcnow(),
                                status="FAILED",
                                message="AI returned no result",
                            )
                            session.add(run_log)

                        await session.commit()

                except Exception as e:
                    logger.error(f"AI auto analysis error for {symbol}: {e}")

        await asyncio.sleep(10)


async def trade_plan_monitor_loop():
    """Monitor approved trade plans for SL/TP hits."""
    while True:
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(TradePlan).where(TradePlan.status == "APPROVED")
            )
            active_plans = result.scalars().all()

            for plan in active_plans:
                tick = mt5_client.get_tick(plan.symbol)
                if not tick:
                    continue

                bid = tick["bid"]
                ask = tick["ask"]
                hit = None
                hit_price = 0

                if plan.direction == "BUY":
                    # BUY: check bid against SL and TP
                    if bid <= plan.stop_loss:
                        hit = "SL"
                        hit_price = bid
                    elif bid >= plan.take_profit_1:
                        hit = "TP1"
                        hit_price = bid
                    elif plan.take_profit_2 and bid >= plan.take_profit_2:
                        hit = "TP2"
                        hit_price = bid

                elif plan.direction == "SELL":
                    # SELL: check ask against SL and TP
                    if ask >= plan.stop_loss:
                        hit = "SL"
                        hit_price = ask
                    elif ask <= plan.take_profit_1:
                        hit = "TP1"
                        hit_price = ask
                    elif plan.take_profit_2 and ask <= plan.take_profit_2:
                        hit = "TP2"
                        hit_price = ask

                if hit:
                    # Calculate P/L
                    if plan.direction == "BUY":
                        pl = hit_price - plan.entry_price
                    else:
                        pl = plan.entry_price - hit_price

                    plan.status = "CLOSED"
                    await session.commit()

                    # Send Telegram alert
                    symbol_display = plan.symbol.replace(".m", "")
                    emoji = "🟢" if hit.startswith("TP") else "🔴"
                    result_text = "Take Profit" if hit.startswith("TP") else "Stop Loss"

                    text = (
                        f"{emoji} <b>Trade Closed: {symbol_display}</b>\n\n"
                        f"Direction: <b>{plan.direction}</b>\n"
                        f"Result: <b>{hit} Hit ({result_text})</b>\n\n"
                        f"Entry: <code>{plan.entry_price:.5f}</code>\n"
                        f"Exit: <code>{hit_price:.5f}</code>\n"
                        f"P/L: <b>{'+' if pl >= 0 else ''}{pl:.5f}</b>\n\n"
                        f"SL: <code>{plan.stop_loss:.5f}</code>\n"
                        f"TP1: <code>{plan.take_profit_1:.5f}</code>\n"
                    )
                    if plan.take_profit_2:
                        text += f"TP2: <code>{plan.take_profit_2:.5f}</code>\n"

                    text += f"\nConfidence was: {plan.confidence}%"

                    await telegram_bot.send_message(text)

        await asyncio.sleep(2)


async def broadcast_signal_update(signal_data: dict):
    """Broadcast signal update to /ws/signals connections."""
    message = json.dumps({"type": "signal_update", **signal_data})
    disconnected = []
    for ws in signal_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        signal_connections.remove(ws)


async def alert_monitor_loop():
    """Monitor active AI alerts for SL/TP hits."""
    from app.models import AIMarketSummary
    from sqlalchemy import select

    while True:
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(AIMarketSummary).where(AIMarketSummary.status == "ACTIVE")
                )
                active_alerts = result.scalars().all()

                for alert in active_alerts:
                    if not alert.entry_price or not alert.stop_loss:
                        continue

                    tick = mt5_client.get_tick(alert.symbol)
                    if not tick:
                        continue

                    bid = tick["bid"]
                    ask = tick["ask"]
                    hit = None
                    hit_price = 0.0

                    if alert.direction == "BUY":
                        if bid <= alert.stop_loss:
                            hit = "SL_HIT"
                            hit_price = bid
                        elif alert.take_profit_2 and bid >= alert.take_profit_2:
                            hit = "TP2_HIT"
                            hit_price = bid
                        elif alert.take_profit_1 and bid >= alert.take_profit_1:
                            hit = "TP1_HIT"
                            hit_price = bid

                    elif alert.direction == "SELL":
                        if ask >= alert.stop_loss:
                            hit = "SL_HIT"
                            hit_price = ask
                        elif alert.take_profit_2 and ask <= alert.take_profit_2:
                            hit = "TP2_HIT"
                            hit_price = ask
                        elif alert.take_profit_1 and ask <= alert.take_profit_1:
                            hit = "TP1_HIT"
                            hit_price = ask

                    if hit:
                        if alert.direction == "BUY":
                            pl = hit_price - alert.entry_price
                        else:
                            pl = alert.entry_price - hit_price

                        alert.status = hit
                        alert.exit_price = hit_price
                        alert.exit_reason = hit
                        alert.resolved_at = datetime.utcnow()
                        alert.profit_loss = round(pl, 5)
                        await session.commit()

                        # Telegram notification
                        symbol_display = alert.symbol.replace(".m", "")
                        emoji = "🟢" if "TP" in hit else "🔴"
                        result_text = "Take Profit" if "TP" in hit else "Stop Loss"

                        text = (
                            f"{emoji} <b>AI Alert Resolved: {symbol_display}</b>\n\n"
                            f"Direction: <b>{alert.direction}</b>\n"
                            f"Result: <b>{hit} ({result_text})</b>\n\n"
                            f"Entry: <code>{alert.entry_price:.5f}</code>\n"
                            f"Exit: <code>{hit_price:.5f}</code>\n"
                            f"P/L: <b>{'+' if pl >= 0 else ''}{pl:.5f}</b>\n\n"
                            f"SL: <code>{alert.stop_loss:.5f}</code>\n"
                            f"TP1: <code>{alert.take_profit_1:.5f}</code>\n"
                        )
                        if alert.take_profit_2:
                            text += f"TP2: <code>{alert.take_profit_2:.5f}</code>\n"

                        text += f"\nAI Confidence was: {alert.ai_confidence}%"

                        await telegram_bot.send_message(text)

        except Exception as e:
            logger.error(f"Alert monitor error: {e}")

        await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    await init_db()
    connected = mt5_client.initialize()
    if connected:
        logger.info("MT5 connected successfully")
    else:
        logger.warning("MT5 connection failed - running in degraded mode")

    tasks = []
    if connected:
        tasks.append(asyncio.create_task(tick_broadcast_loop()))
        tasks.append(asyncio.create_task(tick_save_loop()))
        tasks.append(asyncio.create_task(signal_check_loop()))
        tasks.append(asyncio.create_task(ai_analysis_loop()))
        tasks.append(asyncio.create_task(trade_plan_monitor_loop()))
        tasks.append(asyncio.create_task(alert_monitor_loop()))

    yield

    for t in tasks:
        t.cancel()
    mt5_client.shutdown()


app = FastAPI(title="Trade Analysis Dashboard", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(signals.router)
app.include_router(ai.router)
app.include_router(trade_plans.router)
app.include_router(agent.router)


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            symbols = data.get("symbols", [])
            if action == "subscribe":
                ws_manager.subscribe(websocket, symbols)
            elif action == "unsubscribe":
                ws_manager.unsubscribe(websocket, symbols)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await websocket.accept()
    signal_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in signal_connections:
            signal_connections.remove(websocket)
    except Exception:
        if websocket in signal_connections:
            signal_connections.remove(websocket)
