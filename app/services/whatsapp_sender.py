import os
from typing import Any, Dict

import httpx

from app.services.formatter import format_weekly_report_text

CALLMEBOT_ENDPOINT = "https://api.callmebot.com/whatsapp.php"


async def send_weekly_report_via_whatsapp(report_payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Formats the report and sends it to the configured WhatsApp number using CallMeBot.
    Returns a status dictionary to describe the outcome.
    """
    provider = os.getenv("WHATSAPP_PROVIDER")
    if provider != "callmebot":
        return {"status": "skipped", "detail": "WhatsApp provider disabled"}

    phone = os.getenv("WA_PHONE")
    api_key = os.getenv("WA_API_KEY")
    sender = os.getenv("WA_SENDER_NAME") or ""

    if not phone or not api_key:
        return {"status": "skipped", "detail": "Missing CallMeBot credentials"}

    text = format_weekly_report_text(report_payload).strip()
    if not text:
        return {"status": "skipped", "detail": "Empty report payload"}

    params = {
        "phone": phone,
        "text": text,
        "apikey": api_key,
    }
    if sender:
        params["source"] = sender

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(CALLMEBOT_ENDPOINT, params=params)
    except httpx.HTTPError as exc:
        return {"status": "skipped", "detail": f"CallMeBot request failed: {exc}"}

    if response.status_code == 200:
        return {"status": "sent", "detail": "CallMeBot accepted message"}

    detail = f"CallMeBot responded {response.status_code}: {response.text[:200]}"
    return {"status": "skipped", "detail": detail}
