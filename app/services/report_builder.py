"""
Core service that assembles the personalized weekly report for one user.
Pulls structured data from football-data.org and lets the LLM craft the article.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.data.football_provider import (
    get_league_context,
    get_team_context,
)
from app.db import models
from app.news.llm_generator import generate_article


async def build_league_article(
    user_info: Dict[str, str],
    league_code: str,
    subscription_team: Optional[str],
) -> Dict[str, str]:
    """
    Build the article text for one league, including optional team focus.
    """
    league_ctx = await get_league_context(league_code)

    # Ensure we always have a name to display.
    league_name = league_ctx.get("league_name") or league_code

    team_ctx = await get_team_context(subscription_team, league_code)

    favorite_team = user_info.get("favorite_team")
    fan_focus = False
    if favorite_team and subscription_team:
        fan_focus = favorite_team.casefold() == subscription_team.casefold()

    context_for_llm = {
        "user": {
            "name": user_info.get("name") or "Supporter",
            "language": user_info.get("language") or "en",
            "favorite_team": favorite_team,
        },
        "league": _build_league_context_for_llm(
            league_ctx=league_ctx,
            subscription_team=subscription_team,
            team_ctx=team_ctx,
            fan_focus=fan_focus,
        ),
        "team_focus": team_ctx if fan_focus else None,
    }

    try:
        text = await generate_article(context_for_llm)
    except Exception as exc:  # pragma: no cover - guardrail
        text = _fallback_article_text(context_for_llm, error=str(exc))

    return {
        "league_code": league_code,
        "league_name": league_name,
        "text": text,
    }


async def build_user_weekly_report(user_id: str, db: AsyncSession) -> Dict:
    """
    Builds a personalized report for one user.

    Returns:
    {
        "user": {"email": "...", "language": "..."},
        "articles": [
            {"league_code": "...", "league_name": "...", "text": "..."},
            ...
        ]
    }
    """
    # ---------- Fetch user ----------
    result_user = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result_user.scalars().first()
    if not user:
        raise ValueError("User not found")

    # ---------- Fetch subscriptions ----------
    result_subs = await db.execute(
        select(models.Subscription).where(
            models.Subscription.user_id == user_id,
            models.Subscription.is_active == True,  # noqa: E712 - SQLAlchemy style
        )
    )
    subs = result_subs.scalars().all()
    if not subs:
        return {
            "user": {"email": user.email, "language": user.language},
            "articles": [],
        }

    user_info = {
        "language": user.language or "en",
        "name": user.email,
        "favorite_team": user.favorite_team,
    }

    # ---------- Build articles ----------
    articles: List[Dict] = []
    for sub in subs:
        article = await build_league_article(
            user_info=user_info,
            league_code=sub.league,
            subscription_team=sub.team,
        )
        articles.append(article)

    return {
        "user": {
            "email": user.email,
            "language": user.language,
            "favorite_team": user.favorite_team,
        },
        "articles": articles,
    }


def _build_league_context_for_llm(
    league_ctx: Dict[str, Any],
    subscription_team: Optional[str],
    team_ctx: Optional[Dict[str, Any]],
    fan_focus: bool,
) -> Dict[str, Any]:
    table = []
    for row in league_ctx.get("table") or []:
        table.append(
            {
                "rank": row.get("rank"),
                "team": row.get("team"),
                "points": row.get("points"),
            }
        )

    league_payload = {
        "league_code": league_ctx.get("league_code"),
        "league_name": league_ctx.get("league_name"),
        "table": table,
        "fan_focus": fan_focus,
        "subscribed_team": subscription_team,
    }
    if team_ctx:
        league_payload["tracked_team"] = team_ctx
    if league_ctx.get("top_scorers"):
        league_payload["top_scorers"] = league_ctx.get("top_scorers")
    if league_ctx.get("teams"):
        league_payload["teams"] = league_ctx.get("teams")
    return league_payload


def _fallback_article_text(context: Dict[str, Any], error: str | None = None) -> str:
    """
    Deterministic fallback when the LLM cannot be reached.
    Keeps the language rule and basic storytelling alive.
    """
    language = context["user"]["language"]
    league = context["league"]
    league_name = league.get("league_name") or league.get("league_code")
    table = league.get("table") or []
    fan_focus = league.get("fan_focus")
    subscribed_team = league.get("subscribed_team")
    top_scorers = league.get("top_scorers") or []
    tracked_team = league.get("tracked_team")

    leader = table[0]["team"] if table else ("leader" if language == "en" else "leader")
    points = table[0]["points"] if table else ("?" if language == "en" else "?")

    if language == "fr":
        lines = [
            f"{league_name} — Tour d'horizon",
            f"{leader} mène la danse avec {points} points.",
        ]
        if fan_focus and context.get("team_focus"):
            team = context["team_focus"]["team_name"]
            lines.append(_fallback_team_focus_fr(context["team_focus"]))
        elif tracked_team:
            lines.append(_fallback_tracked_team_fr(tracked_team))
        elif subscribed_team:
            lines.append(f"Regardez aussi {subscribed_team}, toujours à la lutte.")
        scorer_line = _format_top_scorers_line("fr", top_scorers)
        if scorer_line:
            lines.append(scorer_line)
        lines.append("À retenir cette semaine : surveille le haut du tableau.")
    else:
        lines = [
            f"{league_name} — Weekly Focus",
            f"{leader} sets the pace with {points} points.",
        ]
        if fan_focus and context.get("team_focus"):
            lines.append(_fallback_team_focus_en(context["team_focus"]))
        elif tracked_team:
            lines.append(_fallback_tracked_team_en(tracked_team))
        elif subscribed_team:
            lines.append(f"Keep tracking {subscribed_team}, still in the conversation.")
        scorer_line = _format_top_scorers_line("en", top_scorers)
        if scorer_line:
            lines.append(scorer_line)
        lines.append("Key point this week: keep an eye on the title race.")

    if error:
        lines.append(f"(fallback: {error})")

    return "\n\n".join(lines)


def _fallback_team_focus_fr(team_focus: Dict[str, Any]) -> str:
    matches = team_focus.get("recent_matches") or []
    mood = _recent_form_summary_fr(matches)
    next_match = team_focus.get("next_match")
    parts = [f"Côté {team_focus.get('team_name', 'le club')}, l'ambiance est {mood}."]
    if next_match:
        opponent = next_match.get("opponent") or "l'adversaire"
        lieu = "à domicile" if next_match.get("home") else "à l'extérieur"
        when = next_match.get("kickoff_utc")
        snippet = f"Prochain rendez-vous {lieu} face à {opponent}"
        if when:
            snippet += f" ({when})"
        snippet += "."
        parts.append(snippet)
    return " ".join(parts)


def _fallback_team_focus_en(team_focus: Dict[str, Any]) -> str:
    matches = team_focus.get("recent_matches") or []
    mood = _recent_form_summary_en(matches)
    next_match = team_focus.get("next_match")
    parts = [f"For {team_focus.get('team_name', 'the club')}, the mood feels {mood}."]
    if next_match:
        opponent = next_match.get("opponent") or "their next opponent"
        venue = "at home" if next_match.get("home") else "away"
        when = next_match.get("kickoff_utc")
        snippet = f"The next test comes {venue} against {opponent}"
        if when:
            snippet += f" ({when})"
        snippet += "."
        parts.append(snippet)
    return " ".join(parts)


def _fallback_tracked_team_fr(team_data: Dict[str, Any]) -> str:
    matches = team_data.get("recent_matches") or []
    mood = _recent_form_summary_fr(matches)
    return f"Suivi de {team_data.get('team_name', 'le club suivi')} : la forme est {mood}."


def _fallback_tracked_team_en(team_data: Dict[str, Any]) -> str:
    matches = team_data.get("recent_matches") or []
    mood = _recent_form_summary_en(matches)
    return f"Tracking {team_data.get('team_name', 'the tracked club')}: form looks {mood}."


def _format_top_scorers_line(language: str, top_scorers: List[Dict[str, Any]]) -> Optional[str]:
    if not top_scorers:
        return None
    highlights = []
    for scorer in top_scorers[:3]:
        player = scorer.get("player")
        team = scorer.get("team")
        goals = scorer.get("goals")
        if player and goals is not None:
            highlights.append(f"{player} ({team}, {goals} buts)" if language == "fr" else f"{player} ({team}, {goals} goals)")
    if not highlights:
        return None
    if language == "fr":
        return "Buteurs en vue : " + ", ".join(highlights) + "."
    return "Hot scorers: " + ", ".join(highlights) + "."
