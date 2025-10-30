from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.db.database import AsyncSessionLocal
from app.services.report_builder import build_user_weekly_report
from app.scheduler.jobs import run_weekly_job_now  # NEW IMPORT

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

@router.get("/news/preview")
async def preview_my_weekly_news(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Build the personalized report for THIS user only.
    """
    try:
        report = await build_user_weekly_report(str(user.id), db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found or no subs")

    return report

@router.post("/news/run-weekly-now")
async def force_weekly_batch(user=Depends(get_current_user)):
    """
    Manual trigger for the full weekly job (all users).
    Useful for live demo in front of jury.
    """
    # later you can check if user.email is you to "authorize"
    await run_weekly_job_now()
    return {"status": "ok", "detail": "weekly batch generated (printed in server logs)"}
