from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.snapshot import Snapshot


async def store_snapshot(
    db: AsyncSession,
    user_id: str,
    league_code: str,
    payload: Dict,
    sources_used: Optional[list] = None,
) -> Snapshot:
    facts_count = len(payload.get("table") or []) + len(payload.get("fixtures_next") or []) + len(payload.get("top_scorers") or [])
    record = Snapshot(
        user_id=str(user_id),
        league_code=league_code.upper(),
        created_at=datetime.now(timezone.utc),
        facts_count=facts_count,
        sources_used=sources_used or payload.get("sources_used") or [],
        payload=payload,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_latest_snapshot_payload(
    db: AsyncSession,
    user_id: str,
    league_code: str,
) -> Optional[Dict]:
    user_id = str(user_id)
    league_code = league_code.upper()
    stmt = (
        select(Snapshot)
        .where(
            Snapshot.user_id == user_id,
            Snapshot.league_code == league_code,
        )
        .order_by(Snapshot.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    snapshot = result.scalars().first()
    if not snapshot:
        return None
    return snapshot.payload
