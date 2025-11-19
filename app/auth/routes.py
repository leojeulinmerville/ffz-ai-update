from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import Optional

from app.services.whatsapp_sender import normalize_fr_phone
from app.auth.security import (
    create_jwt_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.db import AsyncSessionLocal
from app.models.user import User

router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: str = "en"
    favorite_team: str | None = None
    phone_number: Optional[str] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register_user(
    payload: RegisterSchema, db: AsyncSession = Depends(get_db)
):
    normalized_email = payload.email.strip().lower()
    language = (payload.language or "en").lower()
    phone_number = normalize_fr_phone(payload.phone_number)

    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        language=language,
        favorite_team=payload.favorite_team,
        phone_number=phone_number,
    )

    try:
        db.add(user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    await db.refresh(user)
    return {"message": f"User {user.email} registered successfully"}


@router.post("/login")
async def login_user(payload: LoginSchema, db: AsyncSession = Depends(get_db)):
    normalized_email = payload.email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_jwt_token(user.id)
    response = JSONResponse(
        content={"access_token": token, "token_type": "bearer"},
    )
    response.headers["Authorization"] = f"Bearer {token}"
    return response


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language": user.language,
        "favorite_team": user.favorite_team,
        "is_active": user.is_active,
    }
