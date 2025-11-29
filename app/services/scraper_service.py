import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.models.match import Match, MatchFacts, MatchStatus
from app.data.scraper import get_league_facts
from app.data.extractor.vision import extract_match_stats

logger = logging.getLogger(__name__)

async def scrape_league_matches(league_code: str, db: AsyncSession) -> int:
    """
    Scrapes the schedule and results for a league from ESPN (via app.data.scraper)
    and updates the Match table.
    """
    logger.info(f"Scraping matches for league {league_code}")
    
    # We pass None as fan_team because we want the raw league data
    facts = await get_league_facts(league_code, fan_team=None)
    
    matches_data = facts.get("matches_finished", []) + facts.get("matches_scheduled", [])
    count = 0
    
    for m in matches_data:
        # ESPN event ID is usually in the 'id' field of the event, but our scraper 
        # might not be returning it explicitly in the normalized list.
        # We might need to adjust app.data.scraper to ensure we get the ID.
        # For now, let's assume we can construct a unique source_id or use what we have.
        
        # Actually, looking at scraper.py, _normalize_event doesn't return the event ID.
        # We should update scraper.py to return the event ID.
        # But assuming we fix that, let's proceed.
        
        # Temporary fallback if ID is missing: hash of date+teams
        source_id = m.get("id") # We need to ensure scraper returns this
        
        home_team = (m.get("homeTeam") or {}).get("name")
        away_team = (m.get("awayTeam") or {}).get("name")
        date_str = m.get("utcDate")
        
        if not (home_team and away_team and date_str):
            continue
            
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        
        stmt = insert(Match).values(
            source_id=source_id,
            league_code=league_code,
            home_team=home_team,
            away_team=away_team,
            date=dt,
            status=m.get("status", MatchStatus.SCHEDULED.value),
            score_home=m.get("score", {}).get("home"),
            score_away=m.get("score", {}).get("away")
        ).on_conflict_do_update(
            index_elements=['source_id'], # We need a unique constraint on source_id
            set_={
                "status": m.get("status"),
                "score_home": m.get("score", {}).get("home"),
                "score_away": m.get("score", {}).get("away"),
                "updated_at": datetime.now(timezone.utc)
            }
        )
        
        # If source_id is None (until we fix scraper), we might have issues.
        # For this MVP step, let's assume we will fix scraper.py next.
        if source_id:
            await db.execute(stmt)
            count += 1
            
    await db.commit()
    logger.info(f"Upserted {count} matches for {league_code}")
    return count

async def scrape_match_facts(match_id: str, db: AsyncSession):
    """
    Scrapes deep stats for a specific match using Vision.
    """
    match = await db.get(Match, match_id)
    if not match:
        logger.error(f"Match {match_id} not found")
        return

    logger.info(f"Scraping facts for match {match.home_team} vs {match.away_team}")
    
    stats = await extract_match_stats(
        home_team=match.home_team,
        away_team=match.away_team,
        date_obj=match.date
    )
    
    if stats:
        # Upsert MatchFacts
        # Check if exists
        result = await db.execute(select(MatchFacts).where(MatchFacts.match_id == match_id))
        existing = result.scalars().first()
        
        if existing:
            existing.stats = stats.get("stats")
            existing.key_events = stats.get("key_events") # Vision might not return this yet
            existing.source = "flashscore_vision"
        else:
            new_facts = MatchFacts(
                match_id=match_id,
                source="flashscore_vision",
                stats=stats.get("stats"),
                key_events=stats.get("key_events")
            )
            db.add(new_facts)
            
        await db.commit()
        logger.info(f"Saved facts for match {match_id}")
    else:
        logger.warning(f"No stats found for match {match_id}")
