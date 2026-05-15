# Hermes Agent Setup untuk Server Docker

## Overview

Server Anda menggunakan Docker Compose dengan backend di container. Untuk mengaktifkan Hermes Agent, perlu:

1. Buat `.env` file di root project dengan Hermes config
2. Update `docker-compose.yml` untuk pass environment variables ke backend
3. Restart backend container

## Step 1: Buat `.env` di Root Project

File: `/opt/web-live-trade/.env`

```bash
# MT5 Bridge (Windows)
MT5_BRIDGE_URL=http://100.65.56.80:8001

# Frontend URLs
NEXT_PUBLIC_API_URL=http://100.65.56.80:8010
NEXT_PUBLIC_WS_URL=ws://100.65.56.80:8010

# Backend - AI Provider (9router)
ANTHROPIC_BASE_URL=http://10.254.200.211:20128/v1
ANTHROPIC_AUTH_TOKEN=sk_9router
ANTHROPIC_MODEL=claude

# Backend - Hermes Agent (BARU)
HERMES_AGENT_ENABLED=true
HERMES_AGENT_URL=http://10.254.200.211:8090
HERMES_AGENT_TIMEOUT_SECONDS=45
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true
HERMES_AGENT_API_KEY=Dandikurnia!3105

# Backend - Symbols
SYMBOLS=XAUUSD.m,EURUSD.m,GBPUSD.m,BTCUSD.m

# Backend - CORS
ALLOWED_ORIGINS=http://localhost:3000,http://100.65.56.80:3010

# Backend - Telegram (optional)
TELEGRAM_BOT_TOKEN=8638483040:AAEa_whu4o4SYQlThGHJRzCs-xBbJYotrwk
TELEGRAM_CHAT_ID=1730336593
```

## Step 2: Update `docker-compose.yml`

Tambahkan Hermes environment variables ke backend service:

```yaml
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tradebot_backend
    ports:
      - "8010:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://tradebot:tradebot_password@postgres:5432/tradebot
      - MT5_BRIDGE_URL=${MT5_BRIDGE_URL:-}
      - ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL:-http://10.254.200.211:20128/v1}
      - ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN:-sk_9router}
      - ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-claude}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:3001}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}
      - SYMBOLS=${SYMBOLS:-XAUUSD.m,EURUSD.m,GBPUSD.m,BTCUSD.m}
      # Hermes Agent (BARU)
      - HERMES_AGENT_ENABLED=${HERMES_AGENT_ENABLED:-true}
      - HERMES_AGENT_URL=${HERMES_AGENT_URL:-http://10.254.200.211:8090}
      - HERMES_AGENT_TIMEOUT_SECONDS=${HERMES_AGENT_TIMEOUT_SECONDS:-45}
      - HERMES_AGENT_FALLBACK_TO_DIRECT_AI=${HERMES_AGENT_FALLBACK_TO_DIRECT_AI:-true}
      - HERMES_AGENT_API_KEY=${HERMES_AGENT_API_KEY:-}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
```

## Step 3: Restart Backend Container

```bash
cd /opt/web-live-trade

# Pull latest code
git pull origin main

# Restart backend dengan config baru
docker compose restart backend

# Verify backend is running
docker compose logs backend | tail -20
```

## Step 4: Verify Hermes Agent Connected

```bash
# Check agent status
curl http://100.65.56.80:8010/api/agent/status

# Expected response:
# {
#   "enabled": true,
#   "url": "http://10.254.200.211:8090",
#   "connected": true,
#   "timeout_seconds": 45,
#   "fallback_to_direct_ai": true,
#   "last_error": null
# }
```

## Step 5: Test Manual AI Analysis

```bash
# Trigger AI analysis
curl -X POST "http://100.65.56.80:8010/api/ai/analyze/XAUUSD.m"

# Check response includes ai_source field
# Should be: "ai_source": "hermes_agent" or "direct_ai_fallback"
```

## Troubleshooting

### Backend tidak membaca Hermes config

**Check:**
```bash
# Verify .env file exists
ls -la /opt/web-live-trade/.env

# Check backend logs
docker compose logs backend | grep -i hermes
```

**Solution:**
```bash
# Ensure .env file exists dan readable
cat /opt/web-live-trade/.env | grep HERMES

# Restart backend
docker compose restart backend
```

### Hermes Agent not connected

**Check:**
```bash
# Test Hermes connectivity
curl http://10.254.200.211:8090/health

# Check agent status
curl http://100.65.56.80:8010/api/agent/status
```

**Solution:**
1. Verify Hermes Agent server is running
2. Check network connectivity: `ping 10.254.200.211`
3. Check API key is correct in `.env`
4. Increase timeout: `HERMES_AGENT_TIMEOUT_SECONDS=60`

### AI Analysis tidak lewat Hermes

**Check:**
```bash
# Manual trigger
curl -X POST "http://100.65.56.80:8010/api/ai/analyze/XAUUSD.m" | grep ai_source

# Should show: "ai_source": "hermes_agent"
```

**Solution:**
1. Verify `HERMES_AGENT_ENABLED=true` di `.env`
2. Check backend logs: `docker compose logs backend`
3. Verify Hermes is connected: `/api/agent/status`
