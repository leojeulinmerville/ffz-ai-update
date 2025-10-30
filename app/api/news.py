# app/api/news.py

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db import models
from app.auth.security import get_current_user
from app.services.generation_service import generate_and_store_weekly_report
from app.services.report_builder import build_user_weekly_report
from app.services.whatsapp_sender import send_weekly_report_via_whatsapp

router = APIRouter(tags=["news"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/news/preview")
async def preview_news(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    report = await build_user_weekly_report(str(user.id), db)
    return report


@router.post("/news/generate")
async def generate_my_weekly_news(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    result = await generate_and_store_weekly_report(str(user.id), db)
    return result


@router.get("/news/latest")
async def get_my_latest_news(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    q = await db.execute(
        select(models.WeeklyReport)
        .where(models.WeeklyReport.user_id == str(user.id))
        .order_by(models.WeeklyReport.created_at.desc())
        .limit(1)
    )
    row = q.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="No report yet")

    return {
        "report_id": row.id,
        "created_at": row.created_at,
        "delivery_status": row.delivery_status,
        "report": json.loads(row.payload),
    }


@router.post("/news/send_latest")
async def send_my_latest_news(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    q = await db.execute(
        select(models.WeeklyReport)
        .where(models.WeeklyReport.user_id == str(user.id))
        .order_by(models.WeeklyReport.created_at.desc())
        .limit(1)
    )
    row = q.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="No report yet")

    report_payload = json.loads(row.payload)
    status_dict = await send_weekly_report_via_whatsapp(report_payload)
    status_dict["report_id"] = row.id
    return status_dict
