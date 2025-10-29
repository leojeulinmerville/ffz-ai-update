from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db import models
from app.auth.security import hash_password, verify_password, create_jwt_token
from pydantic import BaseModel, EmailStr
from fastapi.responses import JSONResponse

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    language: str = "en"

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register_user(data: RegisterSchema, db: AsyncSession = Depends(get_db)):
    user = models.User(email=data.email, password_hash=hash_password(data.password), language=data.language)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": f"User {user.email} registered successfully"}

@router.post("/login")
async def login_user(data: LoginSchema, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.future import select
    result = await db.execute(select(models.User).where(models.User.email == data.email))
    user = result.scalars().first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_jwt_token(user.id)
    response = JSONResponse(
    content={"access_token": token, "token_type": "bearer"}
)
# Pour Swagger UI (il lira automatiquement ce header)
    response.headers["Authorization"] = f"Bearer {token}"
    return response

from app.auth.security import get_current_user

@router.get("/me")
async def me(user = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "language": user.language, "is_active": user.is_active}


