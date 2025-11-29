import asyncio
import logging
from app.models.db import AsyncSessionLocal
from app.services.scraper_service import scrape_league_matches

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing scraper for PL...")
    async with AsyncSessionLocal() as db:
        count = await scrape_league_matches("PL", db)
        print(f"Scraped {count} matches.")

if __name__ == "__main__":
    asyncio.run(main())
