"""
Context Builder for Report Generation

Fetches and structures data from the database to provide context for LLM report generation.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.match import Match, MatchFacts, MatchStatus

logger = logging.getLogger(__name__)


async def build_team_context(
    team_name: str,
    league_code: str,
    db: AsyncSession,
    weeks: int = 4
) -> Dict[str, Any]:
    """
    Build comprehensive context for a team's weekly report.
    
    Args:
        team_name: Name of the team
        league_code: League code (e.g., 'PL', 'FL1')
        weeks: Number of weeks to look back for recent matches
        db: Database session
    
    Returns:
        Dict with team context including recent matches, stats, form, upcoming fixtures
    """
    logger.info(f"Building context for {team_name} in {league_code}")
    
    # Date range for recent matches
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(weeks=weeks)
    
    # Fetch recent finished matches
    recent_stmt = select(Match).where(
        and_(
            Match.league_code == league_code,
            or_(
                Match.home_team == team_name,
                Match.away_team == team_name
            ),
            Match.status == MatchStatus.FINISHED.value,
            Match.date >= cutoff_date
        )
    ).order_by(Match.date.desc())
    
    recent_result = await db.execute(recent_stmt)
    recent_matches = recent_result.scalars().all()
    
    # Fetch upcoming matches
    upcoming_stmt = select(Match).where(
        and_(
            Match.league_code == league_code,
            or_(
                Match.home_team == team_name,
                Match.away_team == team_name
            ),
            Match.status == MatchStatus.SCHEDULED.value,
            Match.date >= now
        )
    ).order_by(Match.date.asc()).limit(5)
    
    upcoming_result = await db.execute(upcoming_stmt)
    upcoming_matches = upcoming_result.scalars().all()
    
    # Build context
    context = {
        "team_name": team_name,
        "league_code": league_code,
        "league_name": _get_league_name(league_code),
        "recent_matches": [],
        "upcoming_matches": [],
        "form": "",
        "league_position": None  # Will be populated if we have standings data
    }
    
    # Process recent matches
    form_sequence = []
    for match in recent_matches:
        match_data = {
            "home_team": match.home_team,
            "away_team": match.away_team,
            "score_home": match.score_home,
            "score_away": match.score_away,
            "date": match.date.strftime("%Y-%m-%d") if match.date else "",
            "stats": None
        }
        
        # Fetch associated MatchFacts
        facts_stmt = select(MatchFacts).where(MatchFacts.match_id == match.id)
        facts_result = await db.execute(facts_stmt)
        facts = facts_result.scalars().first()
        
        if facts and facts.stats:
            match_data["stats"] = facts.stats
        
        context["recent_matches"].append(match_data)
        
        # Calculate form (W/D/L)
        if match.score_home is not None and match.score_away is not None:
            if match.home_team == team_name:
                if match.score_home > match.score_away:
                    form_sequence.append("W")
                elif match.score_home < match.score_away:
                    form_sequence.append("L")
                else:
                    form_sequence.append("D")
            else:  # away team
                if match.score_away > match.score_home:
                    form_sequence.append("W")
                elif match.score_away < match.score_home:
                    form_sequence.append("L")
                else:
                    form_sequence.append("D")
    
    context["form"] = "-".join(form_sequence) if form_sequence else "No recent matches"
    
    # Process upcoming matches
    for match in upcoming_matches:
        context["upcoming_matches"].append({
            "home_team": match.home_team,
            "away_team": match.away_team,
            "date": match.date.strftime("%Y-%m-%d") if match.date else ""
        })
    
    logger.info(f"Context built: {len(recent_matches)} recent matches, {len(upcoming_matches)} upcoming")
    return context


def _get_league_name(league_code: str) -> str:
    """Map league code to full name."""
    league_names = {
        "PL": "Premier League",
        "FL1": "Ligue 1",
        "PD": "La Liga",
        "BL1": "Bundesliga",
        "SA": "Serie A",
        "CL": "Champions League"
    }
    return league_names.get(league_code, league_code)
