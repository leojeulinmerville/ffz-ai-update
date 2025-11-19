import logging
import os
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.db import AsyncSessionLocal
from app.models.user import User
from app.services.generation_service import generate_and_store_weekly_report

logger = logging.getLogger(__name__)


async def run_weekly_job_once(db: AsyncSession):
    """
    Generate and persist a fresh weekly report for each active user.
    Gère les erreurs de base de données de manière robuste.
    """
    try:
        res_users = await db.execute(
            select(User).where(User.is_active == True)  # noqa: E712
        )
        users = res_users.scalars().all()
    except Exception as exc:
        logger.error(
            "Failed to fetch users from database (schema may not be ready): %s", exc
        )
        return  # Sortie gracieuse si la DB n'est pas prête

    logger.info(
        "Weekly generator starting at %s for %d active users",
        datetime.utcnow().isoformat(),
        len(users),
    )

    for user in users:
        try:
            stored = await generate_and_store_weekly_report(str(user.id), db)
            article_count = len(stored["report"]["articles"])
            logger.info(
                "Generated weekly report for user_id=%s email=%s (%d articles)",
                user.id,
                user.email,
                article_count,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception(
                "Failed to generate weekly report for user_id=%s: %s", user.id, exc
            )


async def run_weekly_job_now():
    """
    Manual trigger helper (can be used elsewhere in the app).
    Gère les erreurs de base de données de manière robuste pour ne pas planter le scheduler.
    """
    try:
        async with AsyncSessionLocal() as db:
            await run_weekly_job_once(db)
    except Exception as exc:
        # Gestion robuste des erreurs : on log mais on ne fait pas planter le scheduler
        logger.exception(
            "Scheduler job failed (database may not be ready): %s. Will retry at next scheduled time.",
            exc
        )


def schedule_jobs(scheduler: AsyncIOScheduler):
    """
    Register the recurring job with APScheduler.
    Devs can override the cadence via FFZ_SCHEDULER_INTERVAL_MINUTES.
    """
    interval_minutes = os.getenv("FFZ_SCHEDULER_INTERVAL_MINUTES")
    if interval_minutes:
        minutes = max(1, int(interval_minutes))
        scheduler.add_job(
            run_weekly_job_now,
            trigger="interval",
            minutes=minutes,
            id="weekly-news-job",
            replace_existing=True,
        )
        logger.info(
            "Scheduler configured with interval trigger (%s minutes)", minutes
        )
        return

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
    logger.info("Scheduler configured for weekly run: Mondays 09:00 Europe/Paris")
