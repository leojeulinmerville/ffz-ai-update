<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> Stashed changes
from __future__ import annotations

import json
import logging
import os
from typing import Dict

from maileroo import EmailAddress, MailerooClient

logger = logging.getLogger(__name__)


class MailerooService:
    def __init__(self) -> None:
        api_key = os.getenv("MAILEROO_API_KEY")
        if not api_key:
            logger.error("MAILEROO_API_KEY missing – cannot send emails.")
            self.client = None
        else:
            self.client = MailerooClient(api_key=api_key)

        # On force bien le bon domaine par défaut
        self.from_email = os.getenv(
            "MAILEROO_DEFAULT_FROM",
            "no-reply@6bc18d7eecc4f6bf.maileroo.org",
        )
        self.from_name = os.getenv("MAILEROO_FROM_NAME", "Football Fan Zone")

        logger.info("Maileroo from_email=%s", self.from_email)

    def send_weekly_email(
        self,
        to_email: str,
        to_name: str | None,
        subject: str,
        html: str,
        text: str,
    ) -> Dict:
        if not self.client:
            return {
                "success": False,
                "reference_id": None,
                "error": "maileroo_not_configured",
            }

        try:
            sender = EmailAddress(address=self.from_email, display_name=self.from_name)
            recipient = EmailAddress(address=to_email, display_name=to_name or to_email)
            payload = {
                "from": sender,
                "to": [recipient],
                "subject": subject,
                "html": html,
                "plain": text,
            }
            reference_id = self.client.send_basic_email(payload)
            logger.info(
                "Maileroo sent weekly email to %s reference=%s",
                to_email,
                reference_id,
            )
            return {"success": True, "reference_id": reference_id}
        except Exception as exc:
            logger.exception("Error sending weekly email to %s", to_email)
            return {
                "success": False,
                "reference_id": None,
                "error": str(exc),
            }


def serialize_email_status(status: Dict) -> str:
    """Sérialise le status de Maileroo pour stockage en base."""
    try:
        return json.dumps(status)
    except Exception:
        return str(status)
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
