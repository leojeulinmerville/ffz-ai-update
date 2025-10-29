from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db import models
from app.auth.security import get_current_user
router = APIRouter()
async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

class SubCreate(BaseModel):
    league: str
    team: str | None = None
    frequency: str = "weekly"

@router.get("/subscriptions")
async def list_subs(user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(models.Subscription).where(models.Subscription.user_id == user.id,
                                                             models.Subscription.is_active == True))
    subs = res.scalars().all()
    return [{"id": str(s.id), "league": s.league, "team": s.team, "frequency": s.frequency} for s in subs]

@router.post("/subscriptions")
async def add_sub(payload: SubCreate, 
                  user = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    sub = models.Subscription(
        user_id=user.id,
        league=payload.league,
        team=payload.team,
        frequency=payload.frequency
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return {
        "id": str(sub.id),
        "league": sub.league,
        "team": sub.team,
        "frequency": sub.frequency
    }

@router.delete("/subscriptions/{sub_id}")
async def delete_sub(sub_id: str, user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(models.Subscription).where(
            models.Subscription.id == sub_id,
            models.Subscription.user_id == user.id
        )
    )
    sub = res.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.is_active = False
    await db.commit()
    return {"status": "ok"}