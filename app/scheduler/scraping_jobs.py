import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db import AsyncSessionLocal
from app.models.match import Match, MatchFacts, MatchStatus
from app.services.scraper_service import scrape_league_matches, scrape_match_facts

logger = logging.getLogger(__name__)

LEAGUES_TO_SCRAPE = ["PL", "FL1", "PD", "BL1", "SA", "CL"]

async def job_scrape_all_leagues():
    """
    Daily job to scrape all configured leagues for schedule and results.
    """
    logger.info("Starting job_scrape_all_leagues")
    async with AsyncSessionLocal() as db:
        for league in LEAGUES_TO_SCRAPE:
            try:
                await scrape_league_matches(league, db)
            except Exception as e:
                logger.error(f"Failed to scrape league {league}: {e}")
    logger.info("Finished job_scrape_all_leagues")

async def job_scrape_recent_matches():
    """
    Hourly job to scrape deep stats for matches that finished recently (last 24h)
    and don't have stats yet.
    """
    logger.info("Starting job_scrape_recent_matches")
    async with AsyncSessionLocal() as db:
        # Find matches finished in last 24h without facts
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Select matches that are FINISHED, recent, and have no facts
        # Note: This query assumes we want to retry if facts are missing.
        # Ideally we should have a 'scraping_status' on Match to avoid infinite retries.
        # For MVP, we'll just check if MatchFacts exists.
        
        stmt = (
            select(Match)
            .outerjoin(MatchFacts)
            .where(
                Match.status == MatchStatus.FINISHED.value,
                Match.date >= since,
                MatchFacts.id == None
            )
        )
        
        result = await db.execute(stmt)
        matches = result.scalars().all()
        
        logger.info(f"Found {len(matches)} matches to scrape facts for")
        
        for match in matches:
            try:
                await scrape_match_facts(match.id, db)
            except Exception as e:
                logger.error(f"Failed to scrape facts for match {match.id}: {e}")
                
    logger.info("Finished job_scrape_recent_matches")
