import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from maileroo import EmailAddress, MailerooClient

from app.services.formatter import format_weekly_report_email

logger = logging.getLogger(__name__)

_MAILEROO_API_KEY = os.getenv("MAILEROO_API_KEY")
_MAILEROO_FROM = os.getenv("MAILEROO_DEFAULT_FROM")
_MAILEROO_FROM_NAME = os.getenv("MAILEROO_FROM_NAME", "Football Fan Zone")

_MAILEROO_CLIENT: Optional[MailerooClient] = None
if _MAILEROO_API_KEY:
    try:
        _MAILEROO_CLIENT = MailerooClient(_MAILEROO_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to initialize Maileroo client: %s", exc)
        _MAILEROO_CLIENT = None


async def _send_basic_email(data: Dict[str, Any]) -> str:
    if not _MAILEROO_CLIENT:
        raise RuntimeError("Maileroo client not initialized")
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _MAILEROO_CLIENT.send_basic_email(data))


async def send_weekly_report_via_email(
    report_payload: Dict[str, Any],
    recipient_email: Optional[str],
    recipient_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deliver the weekly report over email via Maileroo.
    """
    if not recipient_email:
        return {"status": "skipped", "detail": "Missing recipient email"}
    if not (_MAILEROO_CLIENT and _MAILEROO_FROM):
        return {"status": "skipped", "detail": "Maileroo disabled or misconfigured"}

    formatted = format_weekly_report_email(report_payload)
    sender = EmailAddress(_MAILEROO_FROM, _MAILEROO_FROM_NAME)
    recipient = EmailAddress(recipient_email, recipient_name or recipient_email)

    data: Dict[str, Any] = {
        "from": sender,
        "to": [recipient],
        "subject": formatted["subject"],
        "html": formatted["html"],
        "plain": formatted["plain"],
        "tracking": True,
    }

    try:
        reference_id = await _send_basic_email(data)
    except Exception as exc:
        logger.exception("Maileroo email send failed: %s", exc)
        return {"status": "skipped", "detail": str(exc)}

    return {
        "status": "sent",
        "reference_id": reference_id,
        "sent_at": datetime.utcnow().isoformat(),
    }
