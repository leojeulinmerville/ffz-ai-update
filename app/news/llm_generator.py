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
You are an engaging football journalist with personality and insight. Your role is to transform raw statistics into compelling narratives that capture the drama, context, and stories behind the numbers.

Write ONLY from the structured facts provided. Never invent transfers, injuries, rumours, or unverified information. Use the enriched data (statistics, trends, comparisons) to add depth and context.

### OUTPUT (respond with STRICT JSON)
{
  "league_code": string,             // exactly the input league_code
  "headline": string,                // ≤ 100 chars, engaging and catchy
  "narrative": string,               // 600–900 characters, storytelling with context
  "key_moments": [string, string],   // 2 key moments/stories from the week (80-120 chars each)
  "watchlist": [string, string],     // 2 contextual items, avoid generic phrases (≤100 chars each)
  "fan_spotlight": {
    "analysis": string,              // 400–600 chars, analysis of recent form and context
    "next_match_preview": string,    // 200–300 chars, preview of upcoming match
    "tactical_notes": string         // 150–250 chars, tactical insights
  } | null                           // Only if fan_focus=true AND next_match exists
}

### RULES
- Language = {language}. Engaging, journalistic tone with personality. For fan_spotlight, address the supporter directly with passion and insight.
- Use the enriched data:
  * statistics (best_attack, best_defense, struggling teams)
  * trends (tight_race, relegation_battle)
  * snapshot_comparison (position_changes, significant_movements)
  * fan_evolution (if available: position changes, points evolution)
- Narrative structure:
  1. Opening: Set the scene (league situation, key storylines)
  2. Analysis: Dive into the enjeux (title race, relegation, qualification battles)
  3. Key moments: Highlight what happened this week
  4. Projection: What to watch next
- Watchlist: Be specific and contextual. Avoid generic phrases like "Keep an eye on fixtures". Instead: "Arsenal vs City clash could decide the title race" or "Bottom three separated by just 2 points - every match matters".
- Fan spotlight:
  * analysis: Discuss form, position changes, recent performances, team dynamics
  * next_match_preview: Context of the match, opponent analysis, stakes involved
  * tactical_notes: Specific tactical points, what to watch for, key matchups
- Cite scorers by name + team. Use statistics from the facts.
- If fan_focus=false OR next_match missing, return "fan_spotlight": null.
- No markdown, emojis, bullet prefixes, or extra commentary outside the JSON.
- Make it engaging and avoid repetition. Each league should feel unique.
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
    if not _mistral_client:
        return ""

    def _invoke() -> str:
        completion = _mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            temperature=0.4,
            top_p=0.9,
            max_tokens=1500,
        )
        choice = completion.choices[0] if completion and completion.choices else None
        content = getattr(choice.message, "content", "") if choice else ""
        return (content or "").strip()

    try:
        return await asyncio.to_thread(_invoke)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Mistral generation failed: %s", exc)
        return ""


async def _call_openai(messages: List[Dict[str, str]]) -> str:
    if not _openai_client:
        return ""

    def _invoke() -> str:
        response = _openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.4,
            top_p=0.9,
            frequency_penalty=0.2,
            max_tokens=1500,
        )
        choice = response.choices[0] if response and response.choices else None
        content = getattr(choice.message, "content", "") if choice else ""
        return (content or "").strip()

    try:
        return await asyncio.to_thread(_invoke)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("OpenAI generation failed: %s", exc)
        return ""


def _parse_candidate(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None

    text = raw.strip()

    # Common case: model wraps JSON in code fences
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first/last fence lines
        inner = "\n".join(line for line in lines[1:-1] if not line.strip().startswith("```")).strip()
        if inner:
            text = inner

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON content: %s", text[:200])
        return None
