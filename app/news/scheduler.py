from fastapi import APIRouter, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db import models
from app.news.fetcher import fetch_league_standings
from app.news.generator import generate_article

router = APIRouter()
scheduler = AsyncIOScheduler(timezone="Europe/Paris")

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

async def send_weekly_news():
    """Génère un article pour chaque utilisateur abonné."""
    async with AsyncSessionLocal() as db:
        users = (await db.execute(models.User.__table__.select())).all()
        for user in users:
            subs = (await db.execute(models.Subscription.__table__.select()
                                     .where(models.Subscription.user_id == user.id,
                                            models.Subscription.is_active == True))).all()
            for sub in subs:
                standings = await fetch_league_standings(sub.league)
                article = generate_article(user.language, sub.league, standings, sub.team)
                print(f"\n=== Article for {user.email} ===\n{article}\n")

@router.post("/admin/trigger")
async def trigger_now(db: AsyncSession = Depends(get_db)):
    await send_weekly_news()
    return {"status": "triggered"}

def start_scheduler():
    scheduler.add_job(send_weekly_news, "cron", day_of_week="mon", hour=9, minute=0)
    scheduler.start()
