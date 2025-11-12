import asyncio
import logging
import os
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.services.formatter import format_weekly_report_text

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"

WA_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "").lower()
WA_PHONE = os.getenv("WA_PHONE")
WA_API_KEY = os.getenv("WA_API_KEY")
WA_SENDER = os.getenv("WA_SENDER_NAME", "FFZ AI Update")

_CHUNK_SIZE = 950
_SLEEP_BETWEEN = 1.5


def normalize_fr_phone(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("0") and len(digits) >= 9:
        return "+33" + digits[1:]
    if digits.startswith("33"):
        return "+" + digits
    if digits.startswith(("6", "7")) and len(digits) >= 9:
        return "+33" + digits
    return "+" + digits


_PHONE_NORMALIZED = normalize_fr_phone(WA_PHONE)


def _split_chunks(text: str, size: int = _CHUNK_SIZE) -> List[str]:
    text = text.strip()
    if len(text) <= size:
        return [text]

    chunks: List[str] = []
    current = ""

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= size:
            current = paragraph
        else:
            for piece in _split_paragraph(paragraph, size):
                if len(piece) <= size:
                    chunks.append(piece)
                else:
                    chunks.extend(_split_paragraph(piece, size))

    if current:
        chunks.append(current)

    return chunks


def _split_paragraph(paragraph: str, size: int) -> List[str]:
    words = paragraph.split()
    pieces: List[str] = []
    current_words: List[str] = []
    current_len = 0

    for word in words:
        addition = len(word) + (1 if current_words else 0)
        if current_words and current_len + addition > size:
            pieces.append(" ".join(current_words))
            current_words = [word]
            current_len = len(word)
        else:
            current_words.append(word)
            current_len += addition

    if current_words:
        pieces.append(" ".join(current_words))
    return pieces


def _is_success_body(html: str) -> bool:
    html_low = (html or "").lower()
    return (
        "message to:" in html_low
        or "message queued" in html_low
        or "message sent" in html_low
    )


async def _send_chunk_via_callmebot(chunk: str) -> Tuple[bool, str]:
    params = {
        "phone": _PHONE_NORMALIZED,
        "apikey": WA_API_KEY,
        "text": chunk,
    }
    if WA_SENDER:
        params["source"] = WA_SENDER

    encoded = urllib.parse.urlencode(params, safe="")
    url = f"{CALLMEBOT_URL}?{encoded}"

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url)

    ok = 200 <= resp.status_code < 300 and _is_success_body(resp.text)
    return ok, f"HTTP {resp.status_code}: {resp.text[:200]}"


async def send_text(text: str | List[str]) -> Dict[str, Any]:
    if WA_PROVIDER != "callmebot":
        return {"status": "skipped", "detail": "WhatsApp provider disabled"}
    if not (_PHONE_NORMALIZED and WA_API_KEY):
        return {"status": "skipped", "detail": "Missing WA_PHONE/WA_API_KEY"}

    provided_chunks: List[str]
    if isinstance(text, str):
        provided_chunks = [text]
    else:
        provided_chunks = text

    chunks: List[str] = []
    for chunk in provided_chunks:
        normalized = (chunk or "").strip()
        if not normalized:
            continue
        if len(normalized) > _CHUNK_SIZE:
            chunks.extend(_split_chunks(normalized, _CHUNK_SIZE))
        else:
            chunks.append(normalized)

    if not chunks:
        return {"status": "skipped", "detail": "Empty message body"}
    total = len(chunks)
    logger.info("WhatsApp delivery: %d chunk(s)", total)

    statuses = []
    for idx, chunk in enumerate(chunks, start=1):
        ok, info = await _send_chunk_via_callmebot(chunk)
        logger.info(
            "WhatsApp chunk %d/%d len=%d ok=%s info=%s",
            idx,
            total,
            len(chunk),
            ok,
            info,
        )
        statuses.append({"part": idx, "ok": ok, "info": info, "length": len(chunk)})
        if idx < total:
            await asyncio.sleep(_SLEEP_BETWEEN)

    any_success = any(s["ok"] for s in statuses)
    overall_ok = all(s["ok"] for s in statuses) if statuses else False
    status = "sent" if overall_ok else "partial" if any_success else "skipped"

    return {
        "status": status,
        "parts": statuses,
        "sent_at": datetime.utcnow().isoformat(),
    }


async def send_weekly_report_via_whatsapp(report_payload: Dict[str, Any]) -> Dict[str, Any]:
    chunks = format_weekly_report_text(report_payload)
    if not chunks:
        return {"status": "skipped", "detail": "Empty report payload"}
    return await send_text(chunks)
