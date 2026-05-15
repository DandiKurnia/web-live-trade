from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from datetime import datetime
from app.database import Base


class MarketTick(Base):
    __tablename__ = "market_ticks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    spread = Column(Float, nullable=False)
    source = Column(String(20), default="mt5")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TechnicalSnapshot(Base):
    __tablename__ = "technical_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    candle_time = Column(DateTime, nullable=False)
    close_price = Column(Float, nullable=False)
    ema20 = Column(Float, nullable=True)
    ema50 = Column(Float, nullable=True)
    rsi14 = Column(Float, nullable=True)
    atr14 = Column(Float, nullable=True)
    adx14 = Column(Float, nullable=True)
    macd_line = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    ema_distance = Column(Float, nullable=True)
    ema_distance_atr_ratio = Column(Float, nullable=True)
    market_condition = Column(String(30), nullable=True)
    trend = Column(String(30), nullable=True)
    is_closed_candle = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    status = Column(String(30), nullable=False, index=True)
    direction = Column(String(10), nullable=True)
    timeframe = Column(String(10), default="M5")
    confidence = Column(Integer, default=0)
    reason_json = Column(JSON, nullable=True)
    h1_trend = Column(String(30), nullable=True)
    m30_trend = Column(String(30), nullable=True)
    m15_trend = Column(String(30), nullable=True)
    m5_trend = Column(String(30), nullable=True)
    market_condition = Column(String(30), nullable=True)
    rsi14 = Column(Float, nullable=True)
    atr14 = Column(Float, nullable=True)
    adx14 = Column(Float, nullable=True)
    macd_line = Column(Float, nullable=True)
    macd_signal_val = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    ema_distance_atr_ratio = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    nearest_support = Column(Float, nullable=True)
    nearest_resistance = Column(Float, nullable=True)
    distance_to_support = Column(Float, nullable=True)
    distance_to_resistance = Column(Float, nullable=True)
    pullback_status = Column(String(30), nullable=True)
    rejection_candle_status = Column(Boolean, nullable=True)
    blocked_reasons_json = Column(JSON, nullable=True)
    warnings_json = Column(JSON, nullable=True)
    candle_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AIMarketSummary(Base):
    __tablename__ = "ai_market_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    trigger_type = Column(String(10), default="AUTO")
    ai_bias = Column(Text, nullable=True)
    direction = Column(String(10), nullable=True)
    ai_confidence = Column(Integer, default=0)
    recommendation = Column(Text, nullable=True)
    setup_quality = Column(Text, nullable=True)
    entry_price = Column(Float, nullable=True)
    entry_price_source = Column(String(10), nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    entry_reason = Column(Text, nullable=True)
    risk_warning = Column(Text, nullable=True)
    should_create_trade_plan = Column(Boolean, default=False)
    manual_approval_required = Column(Boolean, default=True)
    raw_request_json = Column(JSON, nullable=True)
    raw_response_json = Column(JSON, nullable=True)
    status = Column(String(20), default="INACTIVE", index=True)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(20), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    profit_loss = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AISchedulerRun(Base):
    __tablename__ = "ai_scheduler_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_type = Column(String(10), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="SUCCESS")
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TradePlan(Base):
    __tablename__ = "trade_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit_1 = Column(Float, nullable=False)
    take_profit_2 = Column(Float, nullable=True)
    take_profit_3 = Column(Float, nullable=True)
    risk_reward = Column(Float, nullable=False)
    confidence = Column(Integer, default=0)
    risk_percent = Column(Float, default=1.0)
    lot_size = Column(Float, nullable=True)
    entry_mode = Column(String(20), nullable=True)
    entry_price_source = Column(String(10), nullable=True)
    atr_sl = Column(Float, nullable=True)
    swing_sl = Column(Float, nullable=True)
    final_sl = Column(Float, nullable=True)
    sl_distance = Column(Float, nullable=True)
    min_sl_distance = Column(Float, nullable=True)
    fib_zone_low = Column(Float, nullable=True)
    fib_zone_high = Column(Float, nullable=True)
    pullback_confirmed = Column(Boolean, nullable=True)
    rejection_candle_confirmed = Column(Boolean, nullable=True)
    blocked_reasons_json = Column(JSON, nullable=True)
    reason_json = Column(JSON, nullable=True)
    ai_summary_id = Column(Integer, nullable=True)
    signal_id = Column(Integer, nullable=True)
    manual_approval_required = Column(Boolean, default=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AppLog(Base):
    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
