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

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini")



_mistral_client: Optional[Mistral] = (

    Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None

)

_openai_client: Optional[OpenAI] = (

    OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

)



SYSTEM_PROMPT = """
You are an engaging football journalist with personality and insight. Your role is to transform raw statistics into compelling narratives that capture the drama, context, and stories behind the numbers.

Write ONLY from the structured facts provided. Never invent transfers, injuries, rumours, or unverified information. Use the enriched data (statistics, trends, comparisons) to add depth and context.

### OUTPUT (respond with STRICT JSON only - no code fences)
{
  "league_code": string,             // must echo input facts.league_code
  "headline": string,                // <= 100 chars, engaging and catchy
  "narrative": string,               // ~500-900 chars, storytelling with context
  "key_moments": [string, string],   // exactly 2 items, concrete events from facts
  "watchlist": [string, string],     // exactly 2 items, forward-looking and specific
  "fan_spotlight": {
    "analysis": string,              // analysis of recent form and context (aim for 3-6 sentences)
    "next_match_preview": string,    // preview of upcoming match (1-3 sentences)
    "tactical_notes": string         // tactical insights (1-3 sentences)
  } | null                           // Only if fan_focus=true AND facts has next_match; otherwise null
}

### RULES
- Language = {language}. Use an engaging, journalistic tone with personality. For fan_spotlight, address the supporter directly with passion and insight.
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
- Watchlist: Be specific and contextual. Avoid generic phrases. Make each item actionable and grounded in the facts.
- Fan spotlight (only when fan_spotlight is not null):
  * analysis: Discuss form, position changes, recent performances, team dynamics
  * next_match_preview: Context of the match, opponent analysis, stakes involved
  * tactical_notes: Specific tactical points, what to watch for, key matchups
- Cite scorers by name + team. Use statistics from the facts.
- If fan_focus=false OR next_match missing, return "fan_spotlight": null.
- key_moments and watchlist MUST each have exactly 2 non-empty strings respecting the length ranges above.
- Do NOT include markdown, bullet symbols, code fences, or any text outside the single JSON object.
- Make it engaging and avoid repetition. Each league should feel unique.
"""






async def generate_article(

    facts: Dict[str, Any],

    language: str,

    fan_focus: bool,

) -> Tuple[Dict[str, Any], str]:

    messages = _build_messages(facts, language, fan_focus)

    attempts = int(os.getenv("LLM_MAX_ATTEMPTS", "3"))



    # Force OpenAI first (more reliable JSON), then Mistral if configured

    providers = ["openai", "mistral"]



    for provider in providers:

        for attempt in range(1, attempts + 1):

            raw = None

            if provider == "openai" and _openai_client:

                try:

                    raw = await _call_openai(messages)

                except Exception as exc:  # pragma: no cover - defensive

                    logger.warning("OpenAI generation failed (attempt %s/%s): %s", attempt, attempts, exc)

            elif provider == "mistral" and _mistral_client:

                try:

                    raw = await _call_mistral(messages)

                except Exception as exc:  # pragma: no cover - defensive

                    logger.warning("Mistral generation failed (attempt %s/%s): %s", attempt, attempts, exc)



            if not raw:

                continue



            candidate = _parse_candidate(raw)

            if not _is_candidate_valid(candidate):

                logger.warning("LLM candidate invalid (provider=%s attempt=%s): %s", provider, attempt, raw[:200])

                continue



            article, fallback_used = quality_guard.ensure_article(
                facts, candidate, language, fan_focus
            )
            if fallback_used:
                logger.warning("LLM fallback used after validation (provider=%s attempt=%s) - using fallback output", provider, attempt)
            return article, provider



    raise RuntimeError("LLM generation failed: no valid JSON after retries for both providers.")





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

            response_format={"type": "json_object"},

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

    # Try direct load
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If there is extra chatter, try to extract the first JSON object brace to brace
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                pass
        logger.warning("LLM returned non-JSON content: %s", text[:200])
        return None




def _is_candidate_valid(candidate: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(candidate, dict):
        return False
    if not candidate.get("league_code"):
        return False
    for key in ("headline", "narrative"):
        val = candidate.get(key)
        if not isinstance(val, str) or not val.strip():
            return False
    km = candidate.get("key_moments")
    if not isinstance(km, list) or len(km) < 2:
        return False
    if not all(isinstance(item, str) and item.strip() for item in km[:2]):
        return False
    watchlist = candidate.get("watchlist")
    if not isinstance(watchlist, list) or len(watchlist) < 2:
        return False
    if not all(isinstance(item, str) and item.strip() for item in watchlist[:2]):
        return False
    fan_spotlight = candidate.get("fan_spotlight")
    if fan_spotlight not in (None, {}):
        if not isinstance(fan_spotlight, dict):
            return False
        required_fields = ("analysis", "next_match_preview", "tactical_notes")
        for key in required_fields:
            val = fan_spotlight.get(key)
            if not isinstance(val, str) or not val.strip():
                return False
    return True

