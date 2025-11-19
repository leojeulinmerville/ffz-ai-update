from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.security import get_current_user
from app.data.extractor.leagues import fetch_league_bundle
from app.data.normalizer import bundle_to_facts
from app.data.sources_catalog import get_league_meta
from app.models.db import AsyncSessionLocal
from app.models.user import Subscription
from app.services.snapshots import store_snapshot

router = APIRouter(prefix="/scrape", tags=["scrape"])


class ScrapeRunRequest(BaseModel):
    leagues: list[str] | None = None


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/preview")
async def scrape_preview(league: str = Query(..., description="League code, e.g. FL1")):
    meta = get_league_meta(league)
    if not meta:
        raise HTTPException(status_code=404, detail="Unsupported league code")
    bundle = await fetch_league_bundle(league)
    normalized = bundle_to_facts(bundle)
    payload = normalized.payload
    payload["league_code"] = bundle.meta.code
    payload["league_name"] = bundle.meta.name
    return payload


@router.post("/run")
async def run_snapshot_scrape(
    payload: ScrapeRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    user_id = str(user.id)
    league_code = None
    if payload.leagues:
        league_code = payload.leagues[0].upper()
    else:
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,  # noqa: E712
            )
        )
        sub = result.scalars().first()
        if sub:
            league_code = sub.league
    if not league_code:
        raise HTTPException(status_code=400, detail="No league provided or followed")

    league_code = league_code.upper()
    try:
        bundle = await fetch_league_bundle(league_code)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    normalized = bundle_to_facts(bundle)
    snapshot_payload = normalized.payload
    snapshot_payload["league_code"] = bundle.meta.code
    snapshot_payload["league_name"] = bundle.meta.name
    snapshot_payload.setdefault("sources_used", normalized.sources)

    snapshot = await store_snapshot(
        db,
        user_id,
        league_code,
        snapshot_payload,
        snapshot_payload.get("sources_used"),
    )

    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.league == league_code,
        )
    )
    subscription = result.scalars().first()
    if not subscription:
        subscription = Subscription(
            user_id=user_id,
            league=league_code,
            team=None,
            is_active=True,
        )
        db.add(subscription)
    else:
        subscription.is_active = True

    await db.commit()
    return {"ok": True, "league": league_code, "snapshot_id": snapshot.id}
