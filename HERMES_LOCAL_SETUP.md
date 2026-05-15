# Hermes Agent Local Setup Guide

## Overview

Hermes Agent adalah OpenAI-compatible gateway untuk AI orchestration dalam trading analysis. Untuk local development, ada beberapa opsi setup.

## Current Status

- **Hermes Agent URL**: `http://10.254.200.211:8090`
- **Status**: Connected dan accessible
- **Issue**: Hermes saat ini di-route ke Kiro (development AI) yang menolak trading analysis persona

## Local Setup Options

### Option 1: Use Mock Endpoint (Recommended for Development)

Gunakan mock endpoint untuk testing tanpa perlu Hermes Agent yang fully configured.

#### Setup:
```bash
# backend/.env
HERMES_AGENT_ENABLED=true
HERMES_AGENT_URL=http://10.254.200.211:8090
HERMES_AGENT_TIMEOUT_SECONDS=45
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true
HERMES_AGENT_API_KEY=Dandikurnia!3105
```

#### Test Mock Endpoint:
```bash
curl -X POST "http://localhost:8000/api/agent/trade-analysis/mock" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSD",
    "current_price": {
      "bid": 2375.42,
      "ask": 2375.68
    },
    "signal_engine": {
      "candidate": "BUY",
      "confirmed": true,
      "confidence": 78
    },
    "risk_engine": {
      "allowed": true
    },
    "news_context": {
      "blocked": false
    }
  }'
```

Response:
```json
{
  "success": true,
  "source": "hermes_mock",
  "direction": "BUY",
  "recommendation": "VALID_SETUP",
  "confidence": 78,
  "entry_price_source": "ASK",
  "should_create_trade_plan": true,
  "manual_approval_required": true
}
```

### Option 2: Disable Hermes (Use Direct AI Fallback)

Gunakan direct AI client yang sudah ada tanpa Hermes.

#### Setup:
```bash
# backend/.env
HERMES_AGENT_ENABLED=false
```

#### Test:
```bash
curl http://localhost:8000/api/agent/status
# Response: enabled=false
```

### Option 3: Configure Hermes with Proper Trading Model (Production)

Hermes Agent perlu dikonfigurasi untuk route ke model AI trading yang sebenarnya.

#### Requirements:
1. Hermes Agent server harus route `/v1/chat/completions` ke trading analysis model
2. Model harus return JSON response (bukan text)
3. Model harus respect safety rules (risk engine, manual approval, entry price validation)

#### Configuration:
```bash
# backend/.env
HERMES_AGENT_ENABLED=true
HERMES_AGENT_URL=http://10.254.200.211:8090
HERMES_AGENT_TIMEOUT_SECONDS=45
HERMES_AGENT_FALLBACK_TO_DIRECT_AI=true
HERMES_AGENT_API_KEY=your_actual_api_key
```

## Testing Endpoints

### 1. Check Agent Status
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
  "last_check": "2026-05-15T15:07:18.440654"
}
```

### 2. Check Health (include Hermes)
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "mt5_connected": true,
  "ai_available": true,
  "hermes_agent": {
    "enabled": true,
    "url": "http://10.254.200.211:8090",
    "connected": true,
    "fallback_to_direct_ai": true
  }
}
```

### 3. Test Hermes Health
```bash
curl http://10.254.200.211:8090/health
```

Response:
```json
{
  "status": "ok",
  "platform": "hermes-agent"
}
```

### 4. Test Trade Analysis (Real Hermes)
```bash
curl -X POST "http://localhost:8000/api/agent/trade-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "trade_analysis_second_opinion",
    "symbol": "XAUUSD",
    "current_price": {
      "bid": 2375.42,
      "ask": 2375.68,
      "spread": 0.26
    },
    "signal_engine": {
      "candidate": "BUY",
      "confirmed": true,
      "confidence": 78
    },
    "risk_engine": {
      "allowed": true,
      "blocked_reasons": []
    },
    "news_context": {
      "blocked": false,
      "risk_level": "CLEAR"
    }
  }'
```

### 5. Test Trade Analysis (Mock)
```bash
curl -X POST "http://localhost:8000/api/agent/trade-analysis/mock" \
  -H "Content-Type: application/json" \
  -d '{...same payload...}'
```

## Response Schema

### Success Response
```json
{
  "success": true,
  "source": "hermes_agent",
  "final_bias": "BULLISH",
  "direction": "BUY",
  "recommendation": "VALID_SETUP",
  "confidence": 78,
  "setup_quality": "GOOD",
  "entry_price": 2375.68,
  "entry_price_source": "ASK",
  "should_create_trade_plan": true,
  "manual_approval_required": true,
  "summary": "Strong bullish setup with confirmed signal",
  "entry_reason": "H1 bullish, M15 bullish, ADX confirms trend",
  "risk_warning": "Near minor resistance",
  "validation": {
    "risk_engine_respected": true,
    "schema_valid": true,
    "news_filter_respected": true
  },
  "notes": ["reason 1", "reason 2"]
}
```

### Fallback Response (Hermes Error)
```json
{
  "success": false,
  "source": "hermes_safe_fallback",
  "direction": "WAIT",
  "recommendation": "AVOID",
  "confidence": 0,
  "entry_price_source": "NONE",
  "should_create_trade_plan": false,
  "manual_approval_required": true,
  "summary": "Hermes Agent is unavailable or returned invalid response",
  "validation": {
    "risk_engine_respected": true,
    "schema_valid": false,
    "news_filter_respected": true
  }
}
```

## Troubleshooting

### Hermes not connected
```bash
# Check connectivity
curl http://10.254.200.211:8090/health

# Check backend logs for error details
# Look for "last_error" in /api/agent/status response
```

### JSON parsing error
- Hermes response harus valid JSON atau JSON dalam markdown code block
- Backend akan automatically extract JSON dari ```json...``` format
- Jika masih error, check backend logs

### API Key error
- Pastikan `HERMES_AGENT_API_KEY` benar di `.env`
- Jangan gunakan double quotes jika ada `!` di API key
- Use single quotes: `'Authorization: Bearer key!value'`

### Timeout
- Increase `HERMES_AGENT_TIMEOUT_SECONDS` di `.env`
- Check network connectivity ke Hermes

## Development Workflow

1. **Start with Mock Endpoint**
   - Use `/api/agent/trade-analysis/mock` untuk development
   - No external dependencies
   - Fast iteration

2. **Test with Real Hermes**
   - Once mock works, test with real Hermes
   - Check `/api/agent/status` untuk connectivity

3. **Fallback Testing**
   - Set `HERMES_AGENT_ENABLED=false` untuk test fallback
   - Verify direct AI client works

4. **Integration Testing**
   - Test full flow: signal → Hermes → response → frontend
   - Monitor logs untuk errors

## Files Modified

- `backend/app/hermes_client.py` - Hermes Agent client
- `backend/app/routes/agent.py` - Agent endpoints (including mock)
- `backend/app/routes/health.py` - Health check with Hermes status
- `backend/app/config.py` - Hermes configuration
- `backend/app/main.py` - Include agent routes
- `backend/.env.example` - Hermes environment variables
- `README.md` - Hermes Agent documentation

## Next Steps

1. Configure Hermes Agent server dengan proper trading model
2. Update API key di `.env`
3. Test real Hermes endpoint
4. Integrate dengan frontend UI
5. Monitor production deployment
