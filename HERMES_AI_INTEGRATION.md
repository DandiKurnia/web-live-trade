# Hermes Agent Integration into AI Analysis Flow

## Overview

Semua AI analysis (baik manual trigger maupun auto scheduler) sekarang **harus lewat Hermes Agent terlebih dahulu** sebelum fallback ke direct AI client.

## Architecture

```
Frontend / Signal Engine
    ↓
Manual Trigger: POST /api/ai/analyze/{symbol}
Auto Scheduler: Every N minutes
    ↓
Backend: run_ai_analysis()
    ↓
┌─────────────────────────────────────┐
│ Hermes Agent Integration            │
├─────────────────────────────────────┤
│ 1. If HERMES_AGENT_ENABLED=true     │
│    → Send to Hermes Agent           │
│    → POST /v1/chat/completions      │
│                                     │
│ 2. If Hermes fails & fallback=true  │
│    → Use direct AI client           │
│    → POST to 9router                │
│                                     │
│ 3. If both fail                     │
│    → Return None (no analysis)      │
└─────────────────────────────────────┘
    ↓
Response with ai_source field
    ↓
Database & Frontend
```

## Configuration

### Enable Hermes for All AI Analysis

```bash
# backend/.env
HERMES_AGENT_ENABLED=true
HERMES_AGENT_URL=http://10.254.200.211:8090
HERMES_AGENT_TIMEOUT_SECONDS=45
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true
HERMES_AGENT_API_KEY=Dandikurnia!3105

# AI Analysis Scheduler
AI_ANALYSIS_INTERVAL_MINUTES=15  # Trigger every 15 minutes
AI_ANALYSIS_ALLOWED_MINUTES=0,15,30,45  # At :00, :15, :30, :45
```

### Disable Hermes (Use Direct AI Only)

```bash
# backend/.env
HERMES_AGENT_ENABLED=false
```

## AI Analysis Flow

### 1. Manual Trigger

```bash
curl -X POST "http://localhost:8000/api/ai/analyze/XAUUSD.m"
```

Flow:
1. Backend receives request
2. Builds AI payload from market data
3. Sends to Hermes Agent (if enabled)
4. Hermes returns analysis
5. Response saved to database
6. Returned to frontend

### 2. Auto Scheduler

Backend runs AI analysis automatically every N minutes:
- Checks all configured symbols
- Builds payload for each symbol
- Sends to Hermes Agent
- Saves response to database

### 3. Response Format

```json
{
  "success": true,
  "symbol": "XAUUSD.m",
  "trigger_type": "MANUAL",
  "ai_source": "hermes_agent",
  "ai_bias": "BEARISH",
  "direction": "SELL",
  "ai_confidence": 91,
  "recommendation": "VALID_SETUP",
  "setup_quality": "STRONG",
  "entry_price": 4553.76,
  "entry_price_source": "BID",
  "stop_loss": 4566.0,
  "take_profit_1": 4531.73,
  "take_profit_2": 4517.04,
  "risk_reward": 1.8,
  "summary": "Strong bearish alignment...",
  "entry_reason": "SELL setup is valid because...",
  "risk_warning": "Manual approval is required...",
  "should_create_trade_plan": true,
  "manual_approval_required": true,
  "notes": ["reason 1", "reason 2"],
  "ai_source": "hermes_agent"
}
```

## AI Source Values

| Source | Meaning | When |
|--------|---------|------|
| `hermes_agent` | Hermes Agent returned valid response | Hermes enabled and successful |
| `direct_ai_fallback` | Hermes failed, fell back to direct AI | Hermes failed but fallback enabled |
| `direct_ai` | Direct AI client (Hermes disabled) | HERMES_AGENT_ENABLED=false |
| `hermes_safe_fallback` | Hermes returned invalid response | Hermes response validation failed |

## Testing

### 1. Check Current Configuration

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
  "last_error": null
}
```

### 2. Manual Trigger AI Analysis

```bash
curl -X POST "http://localhost:8000/api/ai/analyze/XAUUSD.m"
```

Check `ai_source` field in response:
- `hermes_agent` → Hermes worked
- `direct_ai_fallback` → Hermes failed, used direct AI
- `direct_ai` → Hermes disabled

### 3. Check AI Summary

```bash
curl "http://localhost:8000/api/ai/summary/XAUUSD.m"
```

Response includes `ai_source` field showing which provider was used.

### 4. Monitor Auto Scheduler

Backend logs will show:
```
INFO: Sending AI analysis to Hermes Agent for XAUUSD.m
INFO: Hermes Agent analysis successful for XAUUSD.m
```

Or if fallback:
```
INFO: Hermes fallback triggered, trying direct AI client for XAUUSD.m
```

## Troubleshooting

### AI Analysis Returns `direct_ai_fallback`

**Cause:** Hermes Agent failed, backend fell back to direct AI

**Check:**
```bash
curl http://localhost:8000/api/agent/status
# Check "last_error" field
```

**Solutions:**
1. Verify Hermes Agent is running: `curl http://10.254.200.211:8090/health`
2. Check API key is correct in `.env`
3. Check network connectivity to Hermes
4. Increase timeout: `HERMES_AGENT_TIMEOUT_SECONDS=60`

### AI Analysis Returns `direct_ai`

**Cause:** Hermes Agent is disabled

**Check:**
```bash
curl http://localhost:8000/api/agent/status
# Check "enabled" field
```

**Solution:**
```bash
# Enable Hermes in .env
HERMES_AGENT_ENABLED=true
```

### No AI Analysis Triggered

**Cause:** Scheduler not running or time not matched

**Check:**
```bash
# Current time
date

# Check allowed minutes in .env
# AI_ANALYSIS_ALLOWED_MINUTES=0,15,30,45
# If current minute is not in list, scheduler won't trigger
```

**Solution:**
```bash
# Manual trigger instead
curl -X POST "http://localhost:8000/api/ai/analyze/XAUUSD.m"
```

## Performance Considerations

### Hermes Agent Adds Latency

- Direct AI: ~2-5 seconds
- Hermes Agent: ~5-10 seconds (includes network round-trip)

### Fallback Behavior

If Hermes is slow or fails:
- With fallback enabled: Automatic retry with direct AI (~2-5 seconds more)
- With fallback disabled: Return None (no analysis)

### Optimization

For faster analysis:
1. Reduce `HERMES_AGENT_TIMEOUT_SECONDS` (but not too low)
2. Ensure Hermes Agent server is responsive
3. Use direct AI if Hermes is consistently slow

## Migration from Direct AI to Hermes

### Step 1: Enable Hermes
```bash
HERMES_AGENT_ENABLED=true
```

### Step 2: Test Manual Trigger
```bash
curl -X POST "http://localhost:8000/api/ai/analyze/XAUUSD.m"
# Check ai_source = "hermes_agent"
```

### Step 3: Monitor Auto Scheduler
- Wait for next scheduled analysis
- Check database for ai_source field
- Verify responses are from Hermes

### Step 4: Disable Fallback (Optional)
```bash
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=false
# Now if Hermes fails, analysis returns None instead of falling back
```

## Files Modified

- `backend/app/ai_analysis.py` - Hermes integration
- `backend/app/hermes_client.py` - Hermes client
- `backend/app/routes/agent.py` - Agent endpoints
- `backend/app/config.py` - Hermes config
- `backend/.env.example` - Environment variables

## Next Steps

1. **Verify Hermes is working:**
   ```bash
   curl http://10.254.200.211:8090/health
   ```

2. **Test manual trigger:**
   ```bash
   curl -X POST "http://localhost:8000/api/ai/analyze/XAUUSD.m"
   ```

3. **Monitor auto scheduler:**
   - Wait for next scheduled time
   - Check `/api/ai/summary/{symbol}` for ai_source

4. **Update frontend:**
   - Display ai_source in UI
   - Show which provider analyzed the trade

5. **Production deployment:**
   - Ensure Hermes Agent is properly configured
   - Set appropriate timeout values
   - Monitor fallback usage
