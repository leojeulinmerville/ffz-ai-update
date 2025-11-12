# app/api/news.py

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.db import AsyncSessionLocal
from app.models.user import User
from app.models.weekly_report import WeeklyReport
from app.auth.security import get_current_user
from app.services.generation_service import generate_and_store_weekly_report
from app.services.report_builder import build_user_weekly_report
from app.services.whatsapp_sender import send_weekly_report_via_whatsapp

router = APIRouter(prefix="/news", tags=["news"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/preview")
async def preview_news(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    report = await build_user_weekly_report(str(user.id), db)
    return report


@router.post("/generate")
async def generate_my_weekly_news(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    result = await generate_and_store_weekly_report(str(user.id), db)
    return result


@router.get("/latest")
async def get_my_latest_news(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    q = await db.execute(
        select(WeeklyReport)
            .where(WeeklyReport.user_id == str(user.id))
            .order_by(WeeklyReport.created_at.desc())
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


@router.post("/send_latest")
async def send_my_latest_news(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    q = await db.execute(
        select(WeeklyReport)
            .where(WeeklyReport.user_id == str(user.id))
            .order_by(WeeklyReport.created_at.desc())
            .limit(1)
    )
    row = q.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="No report yet")

    report_payload = json.loads(row.payload)
    status_dict = await send_weekly_report_via_whatsapp(report_payload)

    if status_dict.get("status") in {"sent", "partial"}:
        row.delivered_at = datetime.utcnow()
        row.delivery_channel = "whatsapp"
        row.delivery_status = status_dict.get("status")
        await db.flush()
    else:
        status_dict.setdefault("detail", "WhatsApp delivery skipped")

    await db.commit()
    await db.refresh(row)

    status_dict["report_id"] = row.id
    status_dict.setdefault("delivery_status", row.delivery_status)
    return status_dict
