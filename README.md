# Trade Analysis Dashboard

Live market dashboard + trade analysis for a JustMarkets demo account using a MetaTrader 5 bridge.

> **Disclaimer:** This project is for demo/paper trading and educational use only. It is NOT financial advice. Do not use this for real trading without proper risk management and understanding.

## Architecture

```
┌─────────────┐     WebSocket/REST     ┌──────────────┐     MT5 API     ┌─────────────┐
│   Next.js   │ ◄──────────────────── │   FastAPI    │ ◄────────────── │  MT5        │
│  Frontend   │                        │   Backend    │                  │  Terminal   │
│  (port 3000)│                        │  (port 8000) │                  │  (Windows)  │
└─────────────┘                        └──────┬───────┘                  └─────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │  PostgreSQL  │
                                       │  (port 5432) │
                                       └──────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │   pgAdmin    │
                                       │  (port 5050) │
                                       └──────────────┘
```

### Running Modes

| Mode                     | Description                                | Use Case                                             |
| ------------------------ | ------------------------------------------ | ---------------------------------------------------- |
| **Local Windows**        | MT5 + Backend run on Windows, DB in Docker | Recommended for development                          |
| **Database-only Docker** | Only PostgreSQL + pgAdmin in Docker        | When running backend locally                         |
| **Full Docker**          | All services in Docker                     | Frontend/DB dev (MT5 won't work in Linux containers) |

## Prerequisites

### MetaTrader 5 Setup

1. Download MetaTrader 5 from [MetaTrader 5](https://www.metatrader5.com/en/download)
2. Install and open MetaTrader 5
3. Create a demo account with **JustMarkets**:
   - Open MT5 → File → Open an Account
   - Search for "JustMarkets" or select "JustMarkets-Demo2"
   - Choose "Open a demo account"
   - Fill in your details and note your **login number** and **password**
4. Make sure MT5 is running and logged in before starting the backend

### System Requirements

- Windows 10/11 (for MT5 terminal)
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for database)

## Quick Start

### 1. Start Database (Docker)

```bash
docker compose -f docker-compose.db.yml up -d
```

This starts:

- PostgreSQL on port 5433
- pgAdmin on port 5050

### 2. Start Backend (Local Windows)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` with your MT5 credentials:

```env
MT5_LOGIN=your_mt5_login_number
MT5_PASSWORD=your_mt5_password
MT5_SERVER=JustMarkets-Demo2
DATABASE_URL=postgresql+asyncpg://tradebot:tradebot_password@localhost:5432/tradebot
ALLOWED_ORIGINS=http://localhost:3000
SYMBOLS=XAUUSD,EURUSD,GBPUSD,BTCUSD
TICK_SAVE_INTERVAL_SECONDS=5
```

Run the backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend (Local)

```bash
cd ..
copy .env.example .env.local
npm install
npm run dev
```

The dashboard will be available at http://localhost:3000

### 4. Full Docker Mode (Alternative)

```bash
docker compose up -d --build
```

> **Note:** MT5 connection will NOT work inside Linux Docker containers. The backend will start in degraded mode. Use this only for frontend/database development.

## Accessing pgAdmin

1. Open http://localhost:5050
2. Login:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Register a new server:
   - **Name:** tradebot (any name)
   - **Connection tab:**
     - Host: `postgres` (if in Docker) or `localhost` (if pgAdmin is local)
     - Port: `5432`
     - Database: `tradebot`
     - Username: `tradebot`
     - Password: `tradebot_password`

## API Endpoints

| Method | Endpoint                                       | Description                  |
| ------ | ---------------------------------------------- | ---------------------------- |
| GET    | `/health`                                      | Health check + MT5 status    |
| GET    | `/api/price/{symbol}`                          | Current price for a symbol   |
| GET    | `/api/symbols`                                 | List of configured symbols   |
| GET    | `/api/candles/{symbol}?timeframe=M1&limit=100` | OHLCV candle data            |
| GET    | `/api/signals/{symbol}`                        | Trade signal with indicators |
| GET    | `/api/agent/status`                            | Hermes Agent status          |
| POST   | `/api/agent/trade-analysis`                    | AI trade analysis via Hermes |
| POST   | `/api/agent/news-analysis`                     | News impact analysis         |
| POST   | `/api/agent/validate-response`                 | Validate AI response         |
| WS     | `/ws/market`                                   | Real-time price updates      |

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Get XAUUSD price
curl http://localhost:8000/api/price/XAUUSD

# Get signal
curl http://localhost:8000/api/signals/XAUUSD

# Get candles
curl http://localhost:8000/api/candles/XAUUSD?timeframe=M5&limit=50
```

### WebSocket Usage

Connect to `ws://localhost:8000/ws/market` and send:

```json
{ "action": "subscribe", "symbols": ["XAUUSD", "EURUSD"] }
```

To unsubscribe:

```json
{ "action": "unsubscribe", "symbols": ["XAUUSD"] }
```

## Trade Analysis

The system calculates the following indicators on M5 candles:

- **EMA 20** — Short-term exponential moving average
- **EMA 50** — Medium-term exponential moving average
- **RSI 14** — Relative Strength Index

### Signal Strategy

| Signal   | Condition                  |
| -------- | -------------------------- |
| **BUY**  | EMA20 > EMA50 AND RSI > 50 |
| **SELL** | EMA20 < EMA50 AND RSI < 50 |
| **WAIT** | Mixed or insufficient data |

## Hermes Agent Integration

Hermes Agent is an OpenAI-compatible AI orchestration layer between the Trading Backend and 9router. It provides intelligent analysis and validation of trade setups while respecting risk engine constraints.

### Architecture

```
Frontend
  ↓
Trading Backend
  ↓
Backend endpoints (/api/agent/*)
  ↓
Hermes Agent (/v1/chat/completions)
  ↓
9router
  ↓
AI Model
```

### Important: Hermes is NOT a Direct Endpoint Provider

**Hermes Agent does NOT have these endpoints:**
- ❌ `POST /api/agent/trade-analysis`
- ❌ `POST /api/agent/news-analysis`
- ❌ `POST /api/agent/validate-response`

**Hermes Agent IS an OpenAI-compatible gateway with:**
- ✅ `POST /v1/chat/completions` (OpenAI-compatible endpoint)
- ✅ `GET /health` (health check)

**The Trading Backend exposes these endpoints:**
- ✅ `GET /api/agent/status`
- ✅ `POST /api/agent/trade-analysis`
- ✅ `POST /api/agent/news-analysis`
- ✅ `POST /api/agent/validate-response`

### Configuration

Add these environment variables to `backend/.env`:

```env
HERMES_AGENT_ENABLED=true
HERMES_AGENT_URL=http://10.254.200.211:8090
HERMES_AGENT_TIMEOUT_SECONDS=45
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true
HERMES_AGENT_API_KEY=your_hermes_agent_api_key_here
```

**Important Security Notes:**
- Do NOT expose `HERMES_AGENT_API_KEY` to the frontend
- Do NOT hardcode the API key in source code
- Do NOT commit the real API key to GitHub
- Use only a placeholder value in `.env.example`

### How Backend Calls Hermes

The backend sends requests to Hermes using the OpenAI-compatible endpoint:

```
POST {HERMES_AGENT_URL}/v1/chat/completions

Headers:
Authorization: Bearer {HERMES_AGENT_API_KEY}
Content-Type: application/json

Body:
{
  "model": "hermes-agent",
  "messages": [
    {
      "role": "system",
      "content": "You are Hermes Agent for trading analysis..."
    },
    {
      "role": "user",
      "content": "<trade-analysis JSON payload>"
    }
  ],
  "stream": false
}
```

### Testing Hermes Agent

#### 1. Health Check

```bash
curl http://10.254.200.211:8090/health
```

Expected response:
```json
{
  "status": "ok",
  "platform": "hermes-agent"
}
```

#### 2. Direct Hermes Chat Completion Test

```bash
curl -s "http://10.254.200.211:8090/v1/chat/completions" \
  -H 'Authorization: Bearer your_hermes_agent_api_key_here' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "hermes-agent",
    "messages": [
      {
        "role": "user",
        "content": "Jawab hanya: HERMES_9ROUTER_OK"
      }
    ],
    "stream": false
  }'
```

Expected response content: `HERMES_9ROUTER_OK`

**Important Bash Note:** If the API key contains an exclamation mark, use single quotes:
```bash
# Wrong (will fail):
-H "Authorization: Bearer Dandikurnia!3105"

# Correct:
-H 'Authorization: Bearer Dandikurnia!3105'
```

#### 3. Backend Trade Analysis Endpoint

```bash
curl -X POST "http://localhost:8000/api/agent/trade-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "trade_analysis_second_opinion",
    "symbol": "XAUUSD",
    "current_price": {
      "bid": 2375.42,
      "ask": 2375.68,
      "spread": 0.26,
      "time": "2026-05-15T14:30:00+07:00"
    },
    "technical_analysis": {
      "h1_trend": "BULLISH_STRONG",
      "m15_trend": "BULLISH_STRONG",
      "m5_trend": "BULLISH_WEAK",
      "rsi14": 56.2,
      "atr14": 1.8,
      "adx14": 26.4,
      "macd_status": "BULLISH",
      "market_condition": "TRENDING",
      "support": 2370.50,
      "resistance": 2382.40
    },
    "signal_engine": {
      "status": "PULLBACK_BUY_READY",
      "candidate": "BUY",
      "confirmed": true,
      "confidence": 78,
      "reason": ["H1 bullish", "M15 bullish", "ADX confirms trend"]
    },
    "risk_engine": {
      "allowed": true,
      "blocked_reasons": [],
      "warnings": [],
      "min_confidence": 75,
      "min_risk_reward": 1.8
    },
    "trade_plan_preview": {
      "direction": "BUY",
      "entry_price": 2375.68,
      "entry_price_source": "ASK",
      "stop_loss": 2371.90,
      "take_profit_1": 2379.46,
      "take_profit_2": 2383.24,
      "risk_reward": 2.0
    },
    "news_context": {
      "blocked": false,
      "risk_level": "CLEAR",
      "upcoming_events": []
    }
  }'
```

#### 4. Check Agent Status

```bash
curl http://localhost:8000/api/agent/status
```

Response:
```json
{
  "enabled": true,
  "url": "http://10.254.200.211:8090",
  "connected": true,
  "timeout_seconds": 45,
  "fallback_to_direct_ai": true,
  "last_error": null,
  "last_check": "2026-05-15T14:57:59.930Z"
}
```

### Safety Rules

Hermes Agent enforces these safety rules:

1. **Risk Engine is the highest authority** — Hermes never overrides `risk_engine.allowed=false`
2. **Manual approval always required** — `manual_approval_required` must always be `true`
3. **News filter respected** — If `news_context.blocked=true`, recommend `WAIT` or `AVOID`
4. **Entry price source validation:**
   - BUY must use ASK
   - SELL must use BID
   - WAIT must use NONE
5. **No trade execution** — Hermes only provides analysis, never executes trades

### Fallback Behavior

If Hermes Agent fails:

1. **If `HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true`:**
   - Backend falls back to direct AI client
   - Response includes `"source": "direct_ai_fallback"`

2. **If `HERMES_AGENT_FALLBACK_TO_DIRECT_AI=false`:**
   - Backend returns safe response:
     ```json
     {
       "source": "hermes_unavailable",
       "direction": "WAIT",
       "recommendation": "AVOID",
       "should_create_trade_plan": false
     }
     ```

### Response Schema

Hermes returns analysis in this format:

```json
{
  "success": true,
  "source": "hermes_agent",
  "final_bias": "BULLISH | BEARISH | NEUTRAL",
  "direction": "BUY | SELL | WAIT",
  "recommendation": "VALID_SETUP | WATCH | WAIT | AVOID",
  "confidence": 0,
  "setup_quality": "POOR | FAIR | GOOD | STRONG",
  "entry_price": null,
  "entry_price_source": "ASK | BID | NONE",
  "should_create_trade_plan": false,
  "manual_approval_required": true,
  "summary": "Short market summary.",
  "entry_reason": "Explain why entry is valid or not.",
  "risk_warning": "Short risk warning.",
  "validation": {
    "risk_engine_respected": true,
    "schema_valid": true,
    "news_filter_respected": true
  },
  "notes": ["reason 1", "reason 2"]
}
```

## Troubleshooting

### MT5 initialize failed

- Make sure MetaTrader 5 is installed and running
- Check that the MT5 terminal is logged in to your account
- Verify the MT5 terminal path is accessible

### MT5 login failed

- Double-check `MT5_LOGIN` and `MT5_PASSWORD` in `.env`
- Verify the server name is exactly `JustMarkets-Demo2`
- Make sure your demo account is active

### Symbol not found

- Ensure the symbol is available on your broker (e.g., XAUUSD may be listed as XAUUSDm)
- Check Market Watch in MT5 — right-click → Show All

### No tick data

- The market may be closed (weekends, holidays)
- Check if MT5 shows prices for the symbol

### WebSocket disconnected

- The frontend will automatically fall back to REST polling every 3 seconds
- Check that the backend is running on port 8000
- Check browser console for CORS errors

### PostgreSQL connection failed

- Ensure Docker containers are running: `docker compose -f docker-compose.db.yml ps`
- Check that port 5432 is not used by another service
- Verify `DATABASE_URL` in `.env`

### pgAdmin cannot connect to PostgreSQL

- If both are in Docker, use host `postgres` (container name)
- If pgAdmin is local, use host `localhost`
- Verify credentials match docker-compose values

### CORS error

- Add your frontend URL to `ALLOWED_ORIGINS` in `backend/.env`
- Multiple origins: `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001`

## Roadmap

- [ ] Telegram notification bot
- [ ] Backtesting engine
- [ ] Paper trading simulation
- [ ] Auto order with safety rules
- [ ] Daily loss limit
- [ ] Risk management (position sizing, stop loss)
- [ ] User authentication
- [ ] Multi-account support
- [ ] More indicators (MACD, Bollinger Bands)
- [ ] Price alerts
- [ ] Trade journal
