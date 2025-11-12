from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.security import get_current_user
from app.models.db import AsyncSessionLocal
from app.models.user import Subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class SubscriptionCreate(BaseModel):
    league: str
    team: str | None = None
    frequency: str = "weekly"


class BulkFollowRequest(BaseModel):
    leagues: List[str]
    frequency: str = "weekly"


@router.get("")
async def list_subscriptions(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    subscriptions = result.scalars().all()
    return [
        {
            "id": str(sub.id),
            "league": sub.league,
            "team": sub.team,
            "frequency": sub.frequency,
        }
        for sub in subscriptions
    ]


@router.post("")
async def add_subscription(
    payload: SubscriptionCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subscription = Subscription(
        user_id=user.id,
        league=payload.league,
        team=payload.team,
        frequency=payload.frequency,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return {
        "id": str(subscription.id),
        "league": subscription.league,
        "team": subscription.team,
        "frequency": subscription.frequency,
    }


@router.post("/bulk")
async def add_subscriptions_bulk(
    payload: BulkFollowRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    created: List[str] = []
    if not payload.leagues:
        return {"created": created}

    for raw_code in payload.leagues:
        if not raw_code:
            continue
        league_code = raw_code.upper()
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.league == league_code,
            )
        )
        subscription = result.scalars().first()
        if subscription and subscription.is_active:
            continue
        if subscription:
            subscription.is_active = True
            subscription.frequency = payload.frequency
        else:
            subscription = Subscription(
                user_id=user.id,
                league=league_code,
                team=None,
                frequency=payload.frequency,
            )
            db.add(subscription)
        created.append(league_code)

    await db.commit()
    return {"created": created}


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == user.id,
        )
    )
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription.is_active = False
    await db.commit()
    return {"status": "ok"}
