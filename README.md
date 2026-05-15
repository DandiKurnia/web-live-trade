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
