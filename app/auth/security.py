import bcrypt, jwt, os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db import models

SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
ALGORITHM = "HS256"

# --- Password helpers ---
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# --- JWT ---
def create_jwt_token(user_id, expires_delta: timedelta = timedelta(hours=8)):
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# --- DB session dependency ---
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Current user helper ---
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Extracts current user from JWT token in Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split("Bearer ")[1]
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
