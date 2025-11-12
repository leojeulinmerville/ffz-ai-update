import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weekly_report import WeeklyReport
from app.services.report_builder import build_user_weekly_report


async def generate_and_store_weekly_report(user_id: str, db: AsyncSession):
    """
    1. Build personalized report (fetch standings + call LLM).
    2. Persist it into the WeeklyReport table.
    3. Return the stored snapshot with metadata.
    """
    report_dict = await build_user_weekly_report(user_id, db)

    db_obj = WeeklyReport(
        user_id=user_id,
        language=report_dict["user"]["language"],
        payload=json.dumps(report_dict, ensure_ascii=False),
        delivery_status="generated",
    )

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    return {
        "report_id": db_obj.id,
        "created_at": db_obj.created_at,
        "delivery_status": db_obj.delivery_status,
        "report": report_dict,
    }
