import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from mistralai import Mistral
from openai import OpenAI

logger = logging.getLogger(__name__)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_mistral_client: Optional[Mistral] = Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
_openai_client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = """You are an AI football editorial assistant.
Your job is to write a weekly briefing for one specific fan.

RULES:

Output MUST be written entirely in the target language given in context.user.language ("fr" or "en"). Do not mix languages.

For each league block:
- If league.fan_focus is true, adopt an emotional supporter tone centred on the team described in team_focus.
- If league.fan_focus is false, keep a neutral journalist tone. You may reference league.tracked_team if provided, but remain factual.

Never invent facts or numbers that are not present in the input context JSON. If information is missing, say it is uncertain or yet to be confirmed.

You may interpret trends (for example: "the gap is closing"), but DO NOT fabricate injuries, transfers, quotes, scandals, or match scores.

Do not mention that you are an AI or that you were given structured data.

CONTENT SHAPE:

Start with a header line containing the league name.
Explain the situation at the top of the table (leaders, gap).
If league.fan_focus is true, dedicate a supporter-style paragraph about team_focus (recent form, strengths, weaknesses, why the next match matters).
If league.fan_focus is false and league.tracked_team is provided, you may include a short neutral note about that tracked team.
End each league block with one final line:
- French: "À retenir cette semaine : ..."
- English: "Key point this week: ..."

LENGTH:

Aim for roughly 150 to 220 words per league block.
When multiple leagues are supplied, the overall report should stay between 400 and 650 words in total.

STYLE:

Plain text paragraphs only.
No bullet points.
No Markdown formatting (no **bold**, no headings, no numbered lists).
No emojis.
"""


async def generate_article(context: Dict[str, Any]) -> str:
    """
    Generate the editorial article given a structured context payload.
    Prefer Mistral, fallback to OpenAI, then deterministic text if all fails.
    """
    language = (context.get("user") or {}).get("language") or "en"
    user_message = json.dumps(context, ensure_ascii=False, indent=2)

    if _mistral_client:
        try:
            return await _call_mistral(user_message)
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("Mistral generation failed: %s", exc)

    if _openai_client:
        try:
            return await _call_openai(user_message)
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("OpenAI generation failed: %s", exc)

    logger.error("Falling back to deterministic article for league=%s", (context.get("league") or {}).get("league_code"))
    return _fallback_article(context, language)


async def _call_mistral(user_message: str) -> str:
    def _invoke() -> str:
        completion = _mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=900,
        )
        return completion.choices[0].message.content.strip()

    return await asyncio.to_thread(_invoke)


async def _call_openai(user_message: str) -> str:
    def _invoke() -> str:
        response = _openai_client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.55,
            max_output_tokens=900,
        )
        return response.output_text.strip()

    return await asyncio.to_thread(_invoke)


def _fallback_article(context: Dict[str, Any], language: str) -> str:
    league = context.get("league") or {}
    league_name = league.get("league_name") or league.get("league_code") or "League"
    table = league.get("table") or []
    top_scorers = league.get("top_scorers") or []
    fan_focus = bool(league.get("fan_focus"))
    tracked_team = league.get("tracked_team")
    team_focus = context.get("team_focus")

    leader, runner_up = _extract_top_two(table)
    paragraphs: List[str] = []

    if language == "fr":
        header = f"{league_name} — Point hebdomadaire"
        if leader and runner_up:
            lead = (
                f"{leader['team']} reste en tête avec {leader['points']} points, "
                f"mais {runner_up['team']} demeure au contact."
            )
        elif leader:
            lead = f"{leader['team']} conserve le fauteuil de leader avec {leader['points']} points."
        else:
            lead = "Le haut du classement reste ouvert pour le moment."

        paragraphs.append(header)
        paragraphs.append(lead)

        if table and len(table) > 2:
            third = table[2]["team"]
            paragraphs.append(f"La bataille pour le podium s'intensifie avec {third} qui s'accroche.")

        if fan_focus and team_focus:
            paragraphs.append(_build_team_focus_paragraph_fr(team_focus))
        elif tracked_team:
            paragraphs.append(_build_tracked_team_paragraph_fr(tracked_team))

        scorer_line = _format_top_scorers_line("fr", top_scorers)
        if scorer_line:
            paragraphs.append(scorer_line)

        conclusion = "À retenir cette semaine : rester attentif à la lutte en tête."
    else:
        header = f"{league_name} — Weekly Briefing"
        if leader and runner_up:
            lead = (
                f"{leader['team']} keeps the lead on {leader['points']} points, "
                f"with {runner_up['team']} still breathing down their neck."
            )
        elif leader:
            lead = f"{leader['team']} remains in control with {leader['points']} points."
        else:
            lead = "The summit remains wide open heading into the next fixtures."

        paragraphs.append(header)
        paragraphs.append(lead)

        if table and len(table) > 2:
            third = table[2]["team"]
            paragraphs.append(f"The podium fight stays alive with {third} applying pressure.")

        if fan_focus and team_focus:
            paragraphs.append(_build_team_focus_paragraph_en(team_focus))
        elif tracked_team:
            paragraphs.append(_build_tracked_team_paragraph_en(tracked_team))

        scorer_line = _format_top_scorers_line("en", top_scorers)
        if scorer_line:
            paragraphs.append(scorer_line)

        conclusion = "Key point this week: every point at the summit still matters."

    paragraphs.append(conclusion)
    return "\n\n".join(paragraphs)


def _extract_top_two(table: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    leader = table[0] if table else None
    runner_up = table[1] if len(table) > 1 else None
    return leader, runner_up


def _format_top_scorers_line(language: str, top_scorers: List[Dict[str, Any]]) -> Optional[str]:
    if not top_scorers:
        return None

    highlights = []
    for scorer in top_scorers[:3]:
        player = scorer.get("player")
        team = scorer.get("team")
        goals = scorer.get("goals")
        if not player or goals is None:
            continue
        if language == "fr":
            highlights.append(f"{player} ({team}, {goals} buts)")
        else:
            highlights.append(f"{player} ({team}, {goals} goals)")

    if not highlights:
        return None

    if language == "fr":
        return "Les buteurs en vue : " + ", ".join(highlights) + "."
    return "Hot scorers: " + ", ".join(highlights) + "."


def _build_team_focus_paragraph_fr(team_focus: Dict[str, Any]) -> str:
    name = team_focus.get("team_name") or "le club"
    mood = _recent_form_summary_fr(team_focus.get("recent_matches") or [])
    next_match = team_focus.get("next_match")
    key_players = team_focus.get("key_players") or []

    parts: List[str] = [f"Côté {name}, l'ambiance est {mood}."]

    if next_match:
        opponent = next_match.get("opponent") or "l'adversaire"
        kickoff = next_match.get("kickoff_utc")
        venue = "à domicile" if next_match.get("home") else "à l'extérieur"
        snippet = f"Prochain rendez-vous {venue} face à {opponent}"
        if kickoff:
            snippet += f" ({kickoff})"
        snippet += "."
        parts.append(snippet)

    if key_players:
        highlights = ", ".join(
            f"{player.get('name')} ({player.get('note')})"
            for player in key_players
            if player.get("name")
        )
        if highlights:
            parts.append(f"Joueurs clés à suivre : {highlights}.")

    return " ".join(parts)


def _build_team_focus_paragraph_en(team_focus: Dict[str, Any]) -> str:
    name = team_focus.get("team_name") or "the club"
    mood = _recent_form_summary_en(team_focus.get("recent_matches") or [])
    next_match = team_focus.get("next_match")
    key_players = team_focus.get("key_players") or []

    parts: List[str] = [f"For {name}, the mood feels {mood}."]

    if next_match:
        opponent = next_match.get("opponent") or "their next opponent"
        kickoff = next_match.get("kickoff_utc")
        venue = "at home" if next_match.get("home") else "away"
        snippet = f"The next test comes {venue} against {opponent}"
        if kickoff:
            snippet += f" ({kickoff})"
        snippet += "."
        parts.append(snippet)

    if key_players:
        highlights = ", ".join(
            f"{player.get('name')} ({player.get('note')})"
            for player in key_players
            if player.get("name")
        )
        if highlights:
            parts.append(f"Key players to watch: {highlights}.")

    return " ".join(parts)


def _build_tracked_team_paragraph_fr(team: Dict[str, Any]) -> str:
    name = team.get("team_name") or "le club suivi"
    result = _recent_form_summary_fr(team.get("recent_matches") or [])
    return f"Le suivi de {name} reste mesuré : la dynamique est {result}."


def _build_tracked_team_paragraph_en(team: Dict[str, Any]) -> str:
    name = team.get("team_name") or "the tracked club"
    result = _recent_form_summary_en(team.get("recent_matches") or [])
    return f"Monitoring {name} stays measured: recent form is {result}."


def _recent_form_summary_fr(matches: List[Dict[str, Any]]) -> str:
    if not matches:
        return "à préciser, les données manquent"

    results = "".join(match.get("result", "") for match in matches)
    if results.startswith("WWW"):
        return "en feu après trois succès"
    if results.startswith("WW"):
        return "globalement positive avec une belle dynamique"
    if results.startswith("LL"):
        return "fragile, la confiance est à reconstruire"
    if "D" in results:
        return "irrégulière, il faut stabiliser"
    return "contrastée, difficile à lire"


def _recent_form_summary_en(matches: List[Dict[str, Any]]) -> str:
    if not matches:
        return "unclear with limited data"

    results = "".join(match.get("result", "") for match in matches)
    if results.startswith("WWW"):
        return "red-hot with three straight wins"
    if results.startswith("WW"):
        return "largely positive thanks to recent momentum"
    if results.startswith("LL"):
        return "fragile with confidence dropping"
    if "D" in results:
        return "mixed and searching for consistency"
    return "hard to read, signals stay mixed"
