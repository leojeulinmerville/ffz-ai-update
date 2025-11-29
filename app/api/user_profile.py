from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

from app.auth.security import get_current_user, hash_password
from app.database import get_db
from app.models.user import User, Subscription

router = APIRouter(prefix="/api/user", tags=["user"])

class UpdateProfilePayload(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None
    favorite_team: Optional[str] = None
    phone_number: Optional[str] = None

class UpdatePasswordPayload(BaseModel):
    current_password: str
    new_password: str

class SubscriptionPayload(BaseModel):
    league: str
    team: Optional[str] = None
    frequency: str = "weekly"  # daily, weekly, monthly
    is_active: bool = True

@router.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile with subscriptions"""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscriptions = result.scalars().all()
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language": user.language,
        "favorite_team": user.favorite_team,
        "phone_number": user.phone_number,
        "is_verified": user.is_verified,
        "subscriptions": [
            {
                "id": str(sub.id),
                "league": sub.league,
                "team": sub.team,
                "frequency": getattr(sub, "frequency", "weekly"),
                "is_active": sub.is_active,
            }
            for sub in subscriptions
        ],
    }

@router.put("/profile")
async def update_profile(
    payload: UpdateProfilePayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile and return updated data"""
    # Merge user into current session to avoid detached instance error
    user = await db.merge(user)
    
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.language is not None:
        user.language = payload.language.lower()
    if payload.favorite_team is not None:
        user.favorite_team = payload.favorite_team
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number

    await db.commit()
    await db.refresh(user)
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language": user.language,
        "favorite_team": user.favorite_team,
        "phone_number": user.phone_number,
        "is_verified": user.is_verified,
    }

@router.post("/subscriptions")
async def add_subscription(
    payload: SubscriptionPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new subscription for the current user"""
    subscription = Subscription(
        user_id=user.id,
        league=payload.league,
        team=payload.team,
        is_active=payload.is_active,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return {
        "id": str(subscription.id),
        "league": subscription.league,
        "team": subscription.team,
        "is_active": subscription.is_active,
    }

@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a subscription"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.user_id == user.id,
        )
    )
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.delete(subscription)
    await db.commit()
    return {"message": "Subscription deleted"}

@router.delete("/account")
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user account"""
    result = await db.execute(select(User).where(User.id == user.id))
    user_to_delete = result.scalars().first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user_to_delete)
    await db.commit()
    return {"message": "Account deleted successfully"}
