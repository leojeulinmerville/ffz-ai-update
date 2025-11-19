from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr


class AdminUserPayload(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    language: str
    favorite_team: str
    leagues: List[str]


class AdminUserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    language: str
    favorite_team: Optional[str]
    leagues: List[str]
