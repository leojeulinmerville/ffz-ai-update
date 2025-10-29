import bcrypt, jwt, os
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_jwt_token(user_id, expires_delta: timedelta = timedelta(hours=8)):
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
