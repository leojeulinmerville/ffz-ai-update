import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from mistralai import Mistral
from openai import OpenAI

from app.services import quality_guard

logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_mistral_client: Optional[Mistral] = (
    Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
)
_openai_client: Optional[OpenAI] = (
    OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
)

SYSTEM_PROMPT = """
You are a professional football editorial assistant.
Write ONLY from the structured facts provided (standings/top5, tight gaps, top_scorers, next_match, sources_used). Never invent transfers, injuries, or rumours.

### OUTPUT (respond with STRICT JSON)
{
  "league_code": string,             // exactly the input league_code
  "headline": string,                // ≤ 85 chars, factual, no emojis
  "narrative": string,               // 450–700 characters, WhatsApp-friendly
  "watchlist": [string, string],     // 2 short items (≤80 chars each), plain sentences
  "fan_spotlight": string | null     // 350–550 chars if fan_focus=true AND next_match exists, else null
}

### RULES
- Language = {language}. Neutral press tone except fan_spotlight which addresses the supporter.
- Cite only what appears in the facts (top5, tight_gaps, next_match, top_scorers up to 10 entries).
- Highlight tight gaps, upcoming duels, or scoring races when relevant.
- Mention scorers by name + team (if provided) without inventing stats.
- If fan_focus=false OR next_match missing, return "fan_spotlight": null.
- No markdown, emojis, bullet prefixes, or extra commentary outside the JSON.
"""

async def generate_article(
    facts: Dict[str, Any],
    language: str,
    fan_focus: bool,
) -> Tuple[Dict[str, Any], str]:
    messages = _build_messages(facts, language, fan_focus)

    for provider in ("mistral", "openai"):
        raw = None
        if provider == "mistral" and _mistral_client:
            try:
                raw = await _call_mistral(messages)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Mistral generation failed: %s", exc)
        elif provider == "openai" and _openai_client:
            try:
                raw = await _call_openai(messages)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("OpenAI generation failed: %s", exc)

        if not raw:
            continue

        candidate = _parse_candidate(raw)
        article, fallback_used = quality_guard.ensure_article(
            facts, candidate, language, fan_focus
        )
        if fallback_used:
            return article, "fallback"
        return article, provider

    article = quality_guard.fallback_article(facts, language, fan_focus)
    return article, "fallback"


def _build_messages(facts: Dict[str, Any], language: str, fan_focus: bool) -> List[Dict[str, str]]:
    payload = {
        "language": language,
        "fan_focus": fan_focus,
        "facts": facts,
    }
    user_content = json.dumps(payload, ensure_ascii=False, indent=2)
    language_label = "French" if language == "fr" else "English"
    prompt = SYSTEM_PROMPT.replace("{language}", language_label)
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]


async def _call_mistral(messages: List[Dict[str, str]]) -> str:
    def _invoke() -> str:
        completion = _mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=900,
        )
        return completion.choices[0].message.content.strip()

    return await asyncio.to_thread(_invoke)


async def _call_openai(messages: List[Dict[str, str]]) -> str:
    def _invoke() -> str:
        response = _openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=900,
        )
        return response.choices[0].message.content.strip()

    return await asyncio.to_thread(_invoke)


def _parse_candidate(raw: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON content")
        return None
