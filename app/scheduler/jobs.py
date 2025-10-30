"""
jobs.py
-------
Scheduler logic (weekly run).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import models
from app.services.report_builder import build_user_weekly_report
from app.db.database import AsyncSessionLocal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz


async def run_weekly_job_once(db: AsyncSession):
    """
    Build all user reports (one batch run).
    For now: we just print them in server logs.
    Later: send to WhatsApp / email.
    """
    res_users = await db.execute(
        select(models.User).where(models.User.is_active == True)
    )
    users = res_users.scalars().all()

    for u in users:
        report = await build_user_weekly_report(str(u.id), db)
        print("=== WEEKLY REPORT FOR", u.email, "===")
        for art in report["articles"]:
            print(f"[{art['league_name']}]")
            print(art["text"])
            print("---")
        print("======================================")


async def run_weekly_job_now():
    """
    Helper you can call manually (for demo / admin endpoint).
    Opens its own DB session.
    """
    async with AsyncSessionLocal() as db:
        await run_weekly_job_once(db)


def schedule_jobs(scheduler: AsyncIOScheduler):
    """
    Register cron jobs on the scheduler.
    - Every Monday 09:00 Europe/Paris -> run_weekly_job_now
    """
    paris_tz = pytz.timezone("Europe/Paris")

    scheduler.add_job(
        run_weekly_job_now,
        trigger="cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        timezone=paris_tz,
        id="weekly-news-job",
        replace_existing=True,
    )
