from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr


class AdminUserPayload(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    language: str
    favorite_team: Optional[str] = None
    leagues: List[str]


class AdminUserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: str
    favorite_team: Optional[str] = None
    leagues: List[str]
