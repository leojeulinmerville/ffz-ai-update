"""
Core service that assembles the personalized weekly report for one user.
Pulls structured data from football-data.org and lets the LLM craft the article.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.data.extractor.leagues import fetch_league_bundle
from app.data.normalizer import bundle_to_facts
from app.models.db import AsyncSessionLocal
from app.models.snapshot import Snapshot
from app.models.user import Subscription, User
from app.news.llm_generator import generate_article
from app.services import quality_guard
from app.services.analytics import (
    calculate_statistics,
    identify_trends,
    calculate_team_form,
)
from app.services.snapshot_comparator import (
    compare_snapshots,
    get_team_evolution,
)
from app.services.snapshots import (
    get_latest_snapshot_payload,
    get_previous_snapshot_payload,
    store_snapshot,
)

logger = logging.getLogger(__name__)
_FALLBACK_WARN_RATIO = float(os.getenv("FFZ_FALLBACK_WARN_RATIO", "0.25"))
_PARIS_TZ = ZoneInfo("Europe/Paris")


async def build_league_article(
    user_id: str,
    user_info: Dict[str, str],
    league_code: str,
    subscription_team: Optional[str],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Build the league article using the fact pipeline + LLM.
    """
    language = (user_info.get("language") or "fr").lower()
    favorite_team = user_info.get("favorite_team")

    snapshot_payload = await get_latest_snapshot_payload(db, user_id, league_code)
    if snapshot_payload is None:
        async with AsyncSessionLocal() as temp_session:
            snapshot_payload = await get_latest_snapshot_payload(temp_session, user_id, league_code)
    if not snapshot_payload:
        bundle = await fetch_league_bundle(league_code)
        normalized = bundle_to_facts(bundle)
        snapshot_payload = normalized.payload
        snapshot_payload["league_code"] = bundle.meta.code
        snapshot_payload["league_name"] = bundle.meta.name
        snapshot_payload.setdefault("sources_used", normalized.sources)
        await store_snapshot(db, user_id, league_code, snapshot_payload, snapshot_payload["sources_used"])
        await db.commit()
    
    # Get previous snapshot for comparison
    previous_snapshot = await get_previous_snapshot_payload(db, user_id, league_code)
    
    facts = await _build_llm_facts(snapshot_payload, favorite_team, previous_snapshot, fixtures=snapshot_payload.get("fixtures_next", []))
    fan_focus = bool(facts.get("fan_team"))

    try:
        article, provider = await generate_article(facts, language, fan_focus)
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger = logging.getLogger(__name__)
        logger.exception("generate_article failed for %s: %s", league_code, exc)
        article = quality_guard.fallback_article(facts, language, fan_focus)
        provider = "fallback"

    legacy_text = _compose_legacy_snapshot(article, language)

    return {
        "league_code": league_code,
        "league_name": facts.get("league_name") or league_code,
        "headline": article.get("headline"),
        "narrative": article.get("narrative"),
        "watchlist": article.get("watchlist") or [],
        "fan_spotlight": article.get("fan_spotlight"),
        "facts": facts,
        "sources_used": snapshot_payload.get("sources_used", []),
        "generator_provider": provider,
        "text": legacy_text,
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
    result_user = await db.execute(select(User).where(User.id == user_id))
    user = result_user.scalars().first()
    if not user:
        raise ValueError("User not found")

    # ---------- Fetch subscriptions ----------
    result_subs = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712 - SQLAlchemy style
        )
    )
    subs = result_subs.scalars().all()

    league_targets = [(sub.league, sub.team) for sub in subs]
    if not league_targets:
        league_targets = await _league_targets_from_snapshots(db, user_id)

    if not league_targets:
        return {
            "user": {"email": user.email, "language": user.language},
            "articles": [],
            "health": {
                "status": "empty",
                "fallback_articles": 0,
                "total_articles": 0,
                "fallback_ratio": 0.0,
            },
        }

    user_identifier = str(user.id)
    user_info = {
        "language": user.language or "en",
        "name": user.email,
        "favorite_team": user.favorite_team,
    }

    # ---------- Build articles ----------
    articles: List[Dict] = []
    for league_code, subscription_team in league_targets:
        article = await build_league_article(
            user_id=user_identifier,
            user_info=user_info,
            league_code=league_code,
            subscription_team=subscription_team,
            db=db,
        )
        articles.append(article)

    fallback_count = sum(
        1 for article in articles if article.get("generator_provider") == "fallback"
    )
    health = _build_health(len(articles), fallback_count)
    if health["status"] != "ok":
        logger.warning(
            "Report builder health=%s user=%s fallback=%d/%d",
            health["status"],
            user.email,
            fallback_count,
            len(articles),
        )

    return {
        "user": {
            "email": user.email,
            "language": user.language,
            "favorite_team": user.favorite_team,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "articles": articles,
        "health": health,
    }




def _compose_legacy_snapshot(article: Dict[str, Any], language: str) -> str:
    parts: List[str] = []

    headline = (article.get("headline") or "").strip()
    if headline:
        parts.append(headline)

    narrative = (article.get("narrative") or "").strip()
    if narrative:
        parts.append(narrative)

    fan_spotlight = (article.get("fan_spotlight") or "").strip()
    if fan_spotlight:
        prefix = "Focus club : " if language == "fr" else "Fan spotlight: "
        parts.append(f"{prefix}{fan_spotlight}")

    watchlist = article.get("watchlist") or []
    if watchlist:
        header = "A surveiller :" if language == "fr" else "Watchlist:"
        parts.append(header)
        parts.extend(f"- {item}" for item in watchlist)

    return "\n\n".join(parts)


def _build_health(total: int, fallback_count: int) -> Dict[str, Any]:
    if total <= 0:
        return {
            "status": "empty",
            "fallback_articles": 0,
            "total_articles": 0,
            "fallback_ratio": 0.0,
        }
    ratio = fallback_count / total
    if fallback_count == 0:
        status = "ok"
    elif ratio <= _FALLBACK_WARN_RATIO:
        status = "watch"
    else:
        status = "degraded"
    return {
        "status": status,
        "fallback_articles": fallback_count,
        "total_articles": total,
        "fallback_ratio": round(ratio, 3),
    }


async def _build_llm_facts(
    payload: Dict[str, Any],
    favorite_team: Optional[str],
    previous_snapshot: Optional[Dict[str, Any]] = None,
    fixtures: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    table = [row for row in (payload.get("table") or []) if row.get("team")]
    fixtures = fixtures or payload.get("fixtures_next") or []
    top_rows = table[:5]

    top5: List[Dict[str, Any]] = []
    for idx, row in enumerate(top_rows, start=1):
        top5.append(
            {
                "club": row.get("team"),
                "points": row.get("points"),
                "rank": row.get("rank", idx),
            }
        )

    tight_gaps = _compute_tight_gaps(top5)
    next_match = _find_next_match(fixtures, favorite_team)
    top_scorers = (payload.get("top_scorers") or [])[:10]

    # Calculate enriched statistics
    stats = calculate_statistics(table)
    trends = identify_trends(table)
    
    # Compare with previous snapshot
    snapshot_comparison = compare_snapshots(payload, previous_snapshot)
    
    # Get team evolution if favorite team exists
    fan_evolution = None
    fan_form_data = []
    if favorite_team:
        fan_evolution = get_team_evolution(payload, previous_snapshot, favorite_team)
        # Calculate form (placeholder - will be enhanced when we have match results)
        fan_form_data = calculate_team_form(favorite_team, fixtures)
    
    # Build enriched facts dict
    facts: Dict[str, Any] = {
        "league_code": payload.get("league_code"),
        "league_name": payload.get("league_name"),
        "top5": top5,
        "top_scorers": top_scorers,
        "tight_gaps": tight_gaps,
        "calendar_notes": [],
        "fan_team": favorite_team if next_match else None,
        "fan_form": fan_form_data,
        "next_match": next_match,
        "sources_used": payload.get("sources_used") or [],
        "table": table,
        # Enriched data
        "statistics": stats,
        "trends": trends,
        "snapshot_comparison": snapshot_comparison,
        "fan_evolution": fan_evolution,
    }
    
    return facts


async def _league_targets_from_snapshots(
    db: AsyncSession, user_id: str
) -> List[tuple[str, Optional[str]]]:
    stmt = (
        select(Snapshot.league_code)
        .where(Snapshot.user_id == user_id)
        .order_by(Snapshot.created_at.desc())
    )
    result = await db.execute(stmt)
    seen: set[str] = set()
    targets: List[tuple[str, Optional[str]]] = []
    for code in result.scalars():
        if not code:
            continue
        normalized = code.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        targets.append((normalized, None))
    return targets


def _compute_tight_gaps(top5: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gaps: List[Dict[str, Any]] = []
    for idx in range(len(top5) - 1):
        club_a = top5[idx].get("club")
        club_b = top5[idx + 1].get("club")
        try:
            pts_a = int(top5[idx].get("points"))
            pts_b = int(top5[idx + 1].get("points"))
        except (TypeError, ValueError):
            continue
        diff = abs(pts_a - pts_b)
        if diff <= 2:
            gaps.append(
                {
                    "pos1": idx + 1,
                    "pos2": idx + 2,
                    "gap_points": diff,
                    "club_a": club_a,
                    "club_b": club_b,
                }
            )
    return gaps


def _find_next_match(fixtures: List[Dict[str, Any]], favorite_team: Optional[str]) -> Optional[Dict[str, Any]]:
    if not favorite_team:
        return None

    soonest: Optional[Tuple[datetime, Dict[str, Any]]] = None
    now = datetime.now(timezone.utc)

    for fixture in fixtures:
        home = fixture.get("home")
        away = fixture.get("away")
        if favorite_team not in (home, away):
            continue
        kickoff_raw = fixture.get("kickoff_utc")
        kickoff = _parse_iso(kickoff_raw)
        if not kickoff:
            continue
        if kickoff < now:
            continue
        if not soonest or kickoff < soonest[0]:
            soonest = (kickoff, {"home": home, "away": away, "utc_kickoff": kickoff.isoformat(), "local_kickoff": kickoff.astimezone(_PARIS_TZ).isoformat()})

    return soonest[1] if soonest else None


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
