import httpx
import json
import logging
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)

AI_SYSTEM_PROMPT = """You are a conservative trading analysis assistant for a demo trading dashboard.
You are only a second opinion.
You must not execute trades.
You must not override the rule engine or risk engine.
You must analyze the provided technical indicators, multi-timeframe alignment, current bid/ask price, spread, confidence score, and risk context.

Important entry rules:

- For BUY setup, use current ASK as the entry reference.
- For SELL setup, use current BID as the entry reference.
- If BUY is valid, clearly return direction BUY and include entry_price from ask.
- If SELL is valid, clearly return direction SELL and include entry_price from bid.
- If the setup is not valid, return direction WAIT and entry_price null.
- Do not always return NEUTRAL.
- If H1, M30, M15, and M5 align and confidence is above threshold, you should classify the setup as VALID_SETUP unless risk context blocks it.
- If timeframe alignment is mixed, recommend WAIT.
- If spread is too high, recommend AVOID.
- If confidence is below threshold, recommend WAIT.
- Be conservative, but do not ignore valid technical setups.

Confidence rules:
- Do not return confidence 0 unless data is missing or invalid.
- If data is valid but setup is unclear, confidence should be between 35 and 60.
- If setup is valid, confidence should be above 70.
- If risk blocks setup, recommendation should be AVOID, not VALID_SETUP.

Return strict JSON only. No markdown. No explanation outside JSON.

Required response format:
{
  "ai_bias": "BULLISH | BEARISH | NEUTRAL",
  "direction": "BUY | SELL | WAIT",
  "ai_confidence": 0,
  "recommendation": "WAIT | WATCH | VALID_SETUP | AVOID",
  "setup_quality": "POOR | FAIR | GOOD | STRONG",
  "entry_price": null,
  "entry_price_source": "ASK | BID | NONE",
  "stop_loss": null,
  "take_profit_1": null,
  "take_profit_2": null,
  "risk_reward": null,
  "summary": "Short market summary.",
  "entry_reason": "Explain why entry is valid or why no entry.",
  "risk_warning": "Short risk warning.",
  "should_create_trade_plan": false,
  "manual_approval_required": true,
  "notes": ["reason 1", "reason 2"]
}"""


class AIClient:
    def __init__(self):
        self.base_url = settings.anthropic_base_url
        self.token = settings.anthropic_auth_token
        self.model = settings.anthropic_model
        self._available = True

    @property
    def is_available(self) -> bool:
        return self._available

    async def analyze(self, payload: Dict) -> Optional[Dict]:
        request_body = {
            "model": self.model,
            "max_tokens": 1500,
            "temperature": 0.2,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": AI_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(payload),
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=request_body,
                        headers=headers,
                    )
                    response.raise_for_status()

                    raw_text = response.text

                    # Handle streaming response (SSE format)
                    if raw_text.startswith("data:"):
                        content_parts = []
                        for line in raw_text.split("\n"):
                            line = line.strip()
                            if line.startswith("data:") and line != "data: [DONE]":
                                chunk_str = line[5:].strip()
                                if not chunk_str or chunk_str == "[DONE]":
                                    continue
                                try:
                                    chunk = json.loads(chunk_str)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        content_parts.append(content)
                                except json.JSONDecodeError:
                                    continue
                        text = "".join(content_parts)
                    else:
                        # Non-streaming response
                        data = json.loads(raw_text)
                        choices = data.get("choices", [])
                        if choices:
                            text = choices[0].get("message", {}).get("content", "")
                        else:
                            text = ""

                    if not text:
                        logger.warning(f"AI returned empty content on attempt {attempt + 1}")
                        continue

                    # Clean markdown code blocks if present
                    text = text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()

                    result = json.loads(text)
                    self._available = True
                    return {
                        "response": result,
                        "raw_request": payload,
                        "raw_response": {"content": text},
                    }

            except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"AI request attempt {attempt + 1} failed: {e}")
                if attempt == 0:
                    continue
                self._available = False
                return None

        return None


ai_client = AIClient()
