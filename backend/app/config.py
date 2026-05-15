from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MT5
    mt5_login: int = 0
    mt5_password: str = ""
    mt5_server: str = "JustMarkets-Demo2"
    mt5_bridge_url: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://tradebot:tradebot_password@localhost:5433/tradebot"

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"

    # Symbols
    symbols: str = "XAUUSD.m,EURUSD.m,GBPUSD.m,BTCUSD.m"

    # Scheduling
    live_price_interval_seconds: int = 1
    tick_save_interval_seconds: int = 5
    signal_timeframe: str = "M5"
    ai_analysis_interval_minutes: int = 30

    # Timezone
    app_timezone: str = "Asia/Jakarta"

    # AI scheduler
    ai_analysis_auto_enabled: bool = True
    ai_analysis_allowed_minutes: str = "0,30"
    ai_min_confidence_for_valid_setup: int = 70
    ai_manual_trigger_cooldown_seconds: int = 15

    # ADX
    adx_period: int = 14
    adx_min_trend: float = 20
    adx_strong_trend: float = 25

    # EMA distance
    min_ema_distance_atr_ratio: float = 0.25

    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Support/Resistance
    sr_lookback_short: int = 20
    sr_lookback_long: int = 50
    min_distance_to_sr_atr_ratio: float = 1.2

    # Fibonacci
    fib_lookback: int = 50
    fib_pullback_min: float = 0.382
    fib_pullback_max: float = 0.618

    # Entry mode
    entry_mode: str = "PULLBACK"
    pullback_ema_tolerance_atr_ratio: float = 0.3
    require_rejection_candle: bool = True
    rejection_wick_body_ratio: float = 1.5

    # SL/TP
    atr_sl_multiplier: float = 2.0
    sl_atr_buffer_multiplier: float = 0.3
    min_sl_distance_xauusd: float = 3.0
    min_sl_distance_eurusd: float = 0.0008
    min_sl_distance_gbpusd: float = 0.0010
    min_sl_distance_btcusd: float = 100.0
    tp1_r_multiplier: float = 1.0
    tp2_r_multiplier: float = 2.0
    tp3_r_multiplier: float = 3.0

    # Risk management
    risk_per_trade_percent: float = 1.0
    max_trades_per_day: int = 3
    max_daily_loss_percent: float = 2.0
    min_confidence: int = 75
    min_risk_reward: float = 1.8
    manual_approval_required: bool = True

    # Max spread per symbol (in points)
    max_spread_xauusd: float = 50
    max_spread_eurusd: float = 20
    max_spread_gbpusd: float = 25
    max_spread_btcusd: float = 100

    # AI provider (9router / OpenAI-compatible)
    anthropic_base_url: str = "http://10.254.200.211:20128/v1"
    anthropic_auth_token: str = "sk_9router"
    anthropic_model: str = "claude"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @property
    def symbol_list(self) -> List[str]:
        return [s.strip() for s in self.symbols.split(",")]

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def allowed_minutes_list(self) -> List[int]:
        return [int(m.strip()) for m in self.ai_analysis_allowed_minutes.split(",")]

    def get_max_spread(self, symbol: str) -> float:
        symbol_lower = symbol.lower().replace(".m", "")
        spread_map = {
            "xauusd": self.max_spread_xauusd,
            "eurusd": self.max_spread_eurusd,
            "gbpusd": self.max_spread_gbpusd,
            "btcusd": self.max_spread_btcusd,
        }
        return spread_map.get(symbol_lower, 50)

    def get_min_sl_distance(self, symbol: str) -> float:
        symbol_lower = symbol.lower().replace(".m", "")
        sl_map = {
            "xauusd": self.min_sl_distance_xauusd,
            "eurusd": self.min_sl_distance_eurusd,
            "gbpusd": self.min_sl_distance_gbpusd,
            "btcusd": self.min_sl_distance_btcusd,
        }
        return sl_map.get(symbol_lower, 3.0)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
