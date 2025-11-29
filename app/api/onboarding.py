from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.auth.security import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class PreferencesSchema(BaseModel):
    language: str
    favorite_team: str
    tone: str

@router.post("/preferences")
async def save_preferences(
    prefs: PreferencesSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Update user object
    current_user.language = prefs.language
    current_user.favorite_team = prefs.favorite_team
    current_user.tone = prefs.tone
    
    # If this is the first time setting preferences, we can mark them as active or similar
    # For now, we just save.
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return {"status": "success", "user": {
        "language": current_user.language,
        "favorite_team": current_user.favorite_team,
        "tone": current_user.tone
    }}

@router.get("/options")
async def get_options():
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "Français"},
            {"code": "es", "name": "Español"},
            {"code": "de", "name": "Deutsch"},
            {"code": "it", "name": "Italiano"}
        ],
        "tones": [
            {"value": "fan", "label": "Fan", "description": "Passionate, biased, and emotional."},
            {"value": "neutral", "label": "Neutral", "description": "Objective, balanced, and factual."},
            {"value": "analytic", "label": "Analytic", "description": "Data-driven, tactical, and deep."}
        ]
    }
