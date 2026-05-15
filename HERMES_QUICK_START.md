# Quick Start: Setup Hermes Agent di Server Ubuntu

## TL;DR - 5 Langkah Setup

### 1. Pull Latest Code
```bash
cd /opt/web-live-trade
git pull origin main
```

### 2. Create .env File
```bash
cat > .env << 'EOF'
MT5_BRIDGE_URL=http://100.65.56.80:8001
NEXT_PUBLIC_API_URL=http://100.65.56.80:8010
NEXT_PUBLIC_WS_URL=ws://100.65.56.80:8010
ANTHROPIC_BASE_URL=http://10.254.200.211:20128/v1
ANTHROPIC_AUTH_TOKEN=sk_9router
ANTHROPIC_MODEL=claude
HERMES_AGENT_ENABLED=true
HERMES_AGENT_URL=http://10.254.200.211:8090
HERMES_AGENT_TIMEOUT_SECONDS=45
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true
HERMES_AGENT_API_KEY=Dandikurnia!3105
SYMBOLS=XAUUSD.m,EURUSD.m,GBPUSD.m,BTCUSD.m
ALLOWED_ORIGINS=http://localhost:3000,http://100.65.56.80:3010
TELEGRAM_BOT_TOKEN=8638483040:AAEa_whu4o4SYQlThGHJRzCs-xBbJYotrwk
TELEGRAM_CHAT_ID=1730336593
EOF
```

### 3. Update docker-compose.yml

Edit `docker-compose.yml` dan tambahkan ke backend service → environment section:

```yaml
      # ===== HERMES AGENT (NEW) =====
      - HERMES_AGENT_ENABLED=${HERMES_AGENT_ENABLED:-true}
      - HERMES_AGENT_URL=${HERMES_AGENT_URL:-http://10.254.200.211:8090}
      - HERMES_AGENT_TIMEOUT_SECONDS=${HERMES_AGENT_TIMEOUT_SECONDS:-45}
      - HERMES_AGENT_FALLBACK_TO_DIRECT_AI=${HERMES_AGENT_FALLBACK_TO_DIRECT_AI:-true}
      - HERMES_AGENT_API_KEY=${HERMES_AGENT_API_KEY:-}
      # =============================
```

### 4. Restart Backend
```bash
docker compose restart backend
```

### 5. Verify
```bash
curl http://100.65.56.80:8010/api/agent/status
```

Expected response:
```json
{
  "enabled": true,
  "url": "http://10.254.200.211:8090",
  "connected": true,
  "timeout_seconds": 45,
  "fallback_to_direct_ai": true,
  "last_error": null
}
```

---

## Testing

### Test 1: Manual AI Analysis
```bash
curl -X POST "http://100.65.56.80:8010/api/ai/analyze/XAUUSD.m" | grep ai_source
```

Expected: `"ai_source": "hermes_agent"` atau `"direct_ai_fallback"`

### Test 2: Check AI Summary
```bash
curl "http://100.65.56.80:8010/api/ai/summary/XAUUSD.m" | grep ai_source
```

### Test 3: Check Backend Logs
```bash
docker compose logs backend | grep -i hermes
```

Expected:
```
backend | INFO: Sending AI analysis to Hermes Agent for XAUUSD.m
backend | INFO: Hermes Agent analysis successful for XAUUSD.m
```

---

## Troubleshooting

### Problem: .env file not found
```bash
cat backend/.env
# cat: backend/.env: No such file or directory
```

**Solution:** Create `.env` di root project, bukan di backend folder:
```bash
cat > .env << 'EOF'
...
EOF
```

### Problem: Hermes not connected
```bash
curl http://100.65.56.80:8010/api/agent/status
# "connected": false
```

**Solution:**
1. Check Hermes is running: `curl http://10.254.200.211:8090/health`
2. Check network: `ping 10.254.200.211`
3. Check API key: `cat .env | grep HERMES_AGENT_API_KEY`
4. Restart backend: `docker compose restart backend`

### Problem: AI analysis not using Hermes
```bash
curl -X POST "http://100.65.56.80:8010/api/ai/analyze/XAUUSD.m" | grep ai_source
# "ai_source": "direct_ai"
```

**Solution:**
1. Verify Hermes enabled: `cat .env | grep HERMES_AGENT_ENABLED`
2. Check backend logs: `docker compose logs backend | grep -i hermes`
3. Restart backend: `docker compose restart backend`

---

## Monitoring

### Real-time Backend Logs
```bash
docker compose logs -f backend
```

### Check Hermes Status Every 10 Seconds
```bash
watch -n 10 'curl -s http://100.65.56.80:8010/api/agent/status | grep connected'
```

### Monitor AI Analysis
```bash
watch -n 5 'curl -s http://100.65.56.80:8010/api/ai/summary/XAUUSD.m | grep ai_source'
```

---

## Files Reference

- `HERMES_SERVER_SETUP.md` — Complete setup guide
- `.env.server` — Environment variables template
- `HERMES_AI_INTEGRATION.md` — AI analysis integration
- `HERMES_LOCAL_SETUP.md` — Local development setup
- `README.md` — Main documentation

---

## Next Steps

1. ✅ Create `.env` file
2. ✅ Update `docker-compose.yml`
3. ✅ Restart backend
4. ✅ Verify Hermes connected
5. ✅ Test manual AI analysis
6. ⏳ Wait for auto scheduler (setiap 15 menit)
7. ⏳ Monitor ai_source di responses
