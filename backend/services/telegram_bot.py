"""
BuyBy Trading System — Telegram Alert Sender
Sends formatted trade signals and alerts to a Telegram channel.
"""

import logging

import httpx

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("buyby.telegram")

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


async def send_alert(message: str) -> bool:
    """
    Send a message to the configured Telegram chat.
    Returns True on success, False on failure (never raises).
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("[TELEGRAM] Bot token or chat ID not configured — skipping alert")
        return False

    url = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("[TELEGRAM] Alert sent successfully")
                return True
            else:
                logger.error(f"[TELEGRAM] Failed: {resp.status_code} — {resp.text}")
                return False
    except Exception as e:
        logger.error(f"[TELEGRAM] Error sending alert: {e}")
        return False


def format_signal(signal: dict) -> str:
    """Format a trade signal into a Telegram-friendly HTML message."""
    sig_type = signal.get("type", "UNKNOWN")
    instrument = signal.get("instrument", "—")
    strike = signal.get("strike", 0)
    entry = signal.get("entry", {})
    sl = signal.get("sl", 0)
    t1 = signal.get("t1", 0)
    t2 = signal.get("t2", 0)
    score = signal.get("score", 0)
    max_score = signal.get("maxScore", 0)
    mode = signal.get("mode", "NORMAL")
    rr = signal.get("rr", 0)

    entry_str = f"{entry.get('low', 0):.1f} - {entry.get('high', 0):.1f}" if entry else "—"

    return (
        f"<b>BUYBY SIGNAL: {sig_type}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Instrument: <b>{instrument}</b>\n"
        f"Strike: <b>{strike}</b>\n"
        f"Mode: <code>{mode}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Entry: {entry_str}\n"
        f"SL: {sl:.1f}\n"
        f"T1: {t1:.1f} | T2: {t2:.1f}\n"
        f"R:R = {rr}\n"
        f"Score: {score}/{max_score}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
