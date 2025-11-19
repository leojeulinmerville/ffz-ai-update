from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import AsyncSessionLocal
from app.models.user import Subscription, User
from app.services.generation_service import generate_and_store_weekly_report

logger = logging.getLogger(__name__)


async def _get_eligible_users(session: AsyncSession) -> List[User]:
    stmt = (
        select(User)
        .join(Subscription, Subscription.user_id == User.id)
        .where(
            User.is_active == True,  # noqa: E712
            User.email.isnot(None),
            User.email != "",
            Subscription.is_active == True,  # noqa: E712
            Subscription.frequency == "weekly",
        )
        .distinct()
    )
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def run_weekly_reports_for_all_users(
    session_factory=AsyncSessionLocal,
) -> Dict[str, Any]:
    """Run the weekly report pipeline for every subscribed user."""
    logger.info("Starting weekly report scheduler run")
    summary: Dict[str, Any] = {
        "total_users": 0,
        "success": 0,
        "failed": 0,
        "results": [],
    }

    async with session_factory() as session:
        users = await _get_eligible_users(session)
        summary["total_users"] = len(users)

        for user in users:
            user_id = str(user.id)
            try:
                result = await generate_and_store_weekly_report(user_id, session)
                email_status: Optional[dict] = result.get("email_status")
                summary["results"].append(
                    {
                        "user_id": user_id,
                        "email": user.email,
                        "ok": True,
                        "error": None,
                        "email_status": email_status,
                    }
                )
                summary["success"] += 1
                logger.info("Weekly report generated for user %s", user_id)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.exception("Error while generating weekly report for user %s", user_id)
                summary["results"].append(
                    {
                        "user_id": user_id,
                        "email": user.email,
                        "ok": False,
                        "error": str(exc),
                        "email_status": None,
                    }
                )
                summary["failed"] += 1

    logger.info(
        "Weekly run completed: %s successes / %s total (failed=%s)",
        summary["success"],
        summary["total_users"],
        summary["failed"],
    )
    return summary


async def main() -> None:
    summary = await run_weekly_reports_for_all_users()
    print(
        f"Weekly reports: {summary['success']}/{summary['total_users']} succeeded, "
        f"{summary['failed']} failed"
    )


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
