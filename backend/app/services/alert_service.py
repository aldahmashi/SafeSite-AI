"""
Alert dispatcher.

Sends Telegram messages for HIGH / CRITICAL safety violations.
Cooldown is enforced at the call site (violation_engine / video_processor).

Configuration (via .env):
  TELEGRAM_BOT_TOKEN — bot token from @BotFather
  TELEGRAM_CHAT_ID   — numeric chat/group ID to send alerts to

Both must be set; if either is missing the service silently skips.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# Simple in-process cooldown: (chat_id, violation_type) → last_sent_ts
_last_sent: dict[str, float] = {}
_ALERT_COOLDOWN_SECONDS = 60          # minimum gap between identical alerts


async def send_telegram_alert(message: str, parse_mode: str = "Markdown") -> bool:
    """
    Send a Telegram message.  Returns True on success, False otherwise.
    Silently returns False if bot credentials are not configured.
    """
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    if not token or not chat_id:
        logger.debug("Telegram not configured — skipping alert.")
        return False

    # Cooldown key uses the first 60 chars of the message as a proxy
    key = message[:60]
    now = time.monotonic()
    if now - _last_sent.get(key, 0) < _ALERT_COOLDOWN_SECONDS:
        logger.debug("Telegram alert suppressed by cooldown: %s", key)
        return False
    _last_sent[key] = now

    url = _TELEGRAM_API.format(token=token)
    payload = {"chat_id": chat_id, "text": message, "parse_mode": parse_mode}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram alert sent.")
                return True
            else:
                logger.warning(
                    "Telegram API returned %s: %s",
                    resp.status_code, resp.text[:200],
                )
                return False
    except httpx.RequestError as exc:
        logger.warning("Telegram request failed: %s", exc)
        return False


async def send_incident_alert(
    violation_type: str,
    risk_level: str,
    timestamp: float,
    video_name: Optional[str] = None,
    description: Optional[str] = None,
) -> bool:
    """
    Convenience wrapper for video-processing incidents.
    Only sends for HIGH / CRITICAL risk; silently skips others.
    """
    if risk_level not in ("HIGH", "CRITICAL"):
        return False

    source = f"Video: {video_name}" if video_name else "Live stream"
    msg = (
        f"\U0001f6a8 *SafeSite AI Alert*\n"
        f"{source}\n"
        f"Violation: {violation_type.replace('_', ' ')}\n"
        f"Risk Level: *{risk_level}*\n"
        f"Timestamp: {timestamp:.1f}s"
    )
    if description:
        msg += f"\n_{description}_"

    return await send_telegram_alert(msg)
