import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = bool(self.token and self.chat_id)

    @property
    def base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                    },
                )
                if response.status_code == 200:
                    return True
                logger.warning(f"Telegram send failed: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False

    async def notify_signal_change(self, signal_data: dict):
        symbol = signal_data.get("symbol", "").replace(".m", "")
        status = signal_data.get("status", "")
        direction = signal_data.get("direction", "")
        confidence = signal_data.get("confidence", 0)
        reasons = signal_data.get("reasons", [])

        emoji = "🟢" if direction == "BUY" else "🔴" if direction == "SELL" else "⚪"

        text = (
            f"{emoji} <b>Signal Update: {symbol}</b>\n\n"
            f"Status: <b>{status}</b>\n"
            f"Direction: <b>{direction or 'NONE'}</b>\n"
            f"Confidence: <b>{confidence}%</b>\n"
        )

        if reasons:
            text += "\nReasons:\n"
            for r in reasons[:5]:
                text += f"• {r}\n"

        await self.send_message(text)

    async def notify_plan_ready(self, plan_data: dict):
        symbol = plan_data.get("symbol", "").replace(".m", "")
        direction = plan_data.get("direction", "")
        entry = plan_data.get("entry_price", 0)
        sl = plan_data.get("stop_loss", 0)
        tp1 = plan_data.get("take_profit_1", 0)
        tp2 = plan_data.get("take_profit_2", 0)
        rr = plan_data.get("risk_reward", 0)
        confidence = plan_data.get("confidence", 0)

        emoji = "🟢" if direction == "BUY" else "🔴"

        text = (
            f"{emoji} <b>Trade Plan Ready: {symbol}</b>\n\n"
            f"Direction: <b>{direction}</b>\n"
            f"Entry: <code>{entry:.5f}</code>\n"
            f"Stop Loss: <code>{sl:.5f}</code>\n"
            f"TP1: <code>{tp1:.5f}</code>\n"
            f"TP2: <code>{tp2:.5f}</code>\n"
            f"Risk/Reward: <b>{rr:.2f}</b>\n"
            f"Confidence: <b>{confidence}%</b>\n\n"
            f"⚠️ Manual approval required"
        )

        await self.send_message(text)

    async def notify_ai_analysis(self, result: dict):
        symbol = result.get("symbol", "").replace(".m", "")
        direction = result.get("direction", "WAIT")
        ai_bias = result.get("ai_bias", "NEUTRAL")
        confidence = result.get("ai_confidence", 0)
        recommendation = result.get("recommendation", "WAIT")
        setup_quality = result.get("setup_quality", "")
        entry_price = result.get("entry_price")
        entry_source = result.get("entry_price_source", "NONE")
        sl = result.get("stop_loss")
        tp1 = result.get("take_profit_1")
        tp2 = result.get("take_profit_2")
        rr = result.get("risk_reward")
        summary = result.get("summary", "")
        entry_reason = result.get("entry_reason", "")
        risk_warning = result.get("risk_warning", "")
        trigger = result.get("trigger_type", "AUTO")
        notes = result.get("notes", [])

        emoji = "🟢" if direction == "BUY" else "🔴" if direction == "SELL" else "⚪"
        rec_emoji = "✅" if recommendation == "VALID_SETUP" else "⚠️" if recommendation == "WATCH" else "🚫" if recommendation == "AVOID" else "⏳"

        text = (
            f"🤖 <b>AI Analysis: {symbol}</b> [{trigger}]\n\n"
            f"{emoji} Direction: <b>{direction}</b>\n"
            f"Bias: <b>{ai_bias}</b>\n"
            f"{rec_emoji} Recommendation: <b>{recommendation}</b>\n"
            f"Quality: <b>{setup_quality}</b>\n"
            f"Confidence: <b>{confidence}%</b>\n"
        )

        if entry_price:
            text += (
                f"\n💰 <b>Entry Details:</b>\n"
                f"Entry: <code>{entry_price:.5f}</code> ({entry_source})\n"
            )
            if sl:
                text += f"SL: <code>{sl:.5f}</code>\n"
            if tp1:
                text += f"TP1: <code>{tp1:.5f}</code>\n"
            if tp2:
                text += f"TP2: <code>{tp2:.5f}</code>\n"
            if rr:
                text += f"R:R: <b>{rr:.2f}</b>\n"

        if summary:
            text += f"\n📝 {summary}\n"

        if entry_reason:
            text += f"\n📌 {entry_reason}\n"

        if risk_warning:
            text += f"\n⚠️ {risk_warning}\n"

        if notes:
            text += "\n📋 Notes:\n"
            for n in notes[:4]:
                text += f"• {n}\n"

        await self.send_message(text)


telegram_bot = TelegramBot()
