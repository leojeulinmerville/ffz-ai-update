import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.security import hash_password, create_jwt_token
from app.models.db import AsyncSessionLocal
from app.models.user import User, Subscription
from app.services.email_sender import send_verification_email

router = APIRouter(prefix="/api/public", tags=["public"])

class RegisterPayload(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = "en"
    favorite_team: Optional[str] = None
    leagues: List[str] = []  # New field for league subscriptions

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/register")
async def register_user(
    payload: RegisterPayload, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user with trial started
    new_user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        language=payload.language,
        favorite_team=payload.favorite_team,
        is_active=True,
        is_verified=False,  # Require verification
        trial_started_at=datetime.now(timezone.utc),  # Start 15-day trial
        subscription_status="trial"
    )
    db.add(new_user)
    await db.flush()

    # Add subscriptions
    for league in payload.leagues:
        db.add(Subscription(
            user_id=new_user.id,
            league=league,
            is_active=True
        ))
    
    await db.commit()
    await db.refresh(new_user)

    # Generate verification token (using JWT for simplicity, but could be DB-backed)
    # We'll use a short-lived JWT as the token
    token = create_jwt_token(new_user.id, expires_delta=timedelta(hours=24))
    
    # Send email
    background_tasks.add_task(send_verification_email, new_user.email, token)

    return {"status": "created", "message": "Please check your email to verify your account"}

@router.post("/verify")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    from app.auth.security import decode_jwt
    
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_verified:
        return {"status": "already_verified"}
        
    user.is_verified = True
    await db.commit()
    
    return {"status": "verified"}
