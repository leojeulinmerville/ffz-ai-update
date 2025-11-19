from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.models.db import AsyncSessionLocal
from app.services.snapshots import get_latest_snapshot_payload

router = APIRouter(prefix="/facts", tags=["facts"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/latest")
async def latest_facts(
    league: str = Query(..., description="League code, e.g. FL1"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await get_latest_snapshot_payload(db, str(user.id), league.upper())
    if not payload:
        raise HTTPException(status_code=404, detail="No snapshot for this league")
    return payload
