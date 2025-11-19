import asyncio
from typing import Any, Dict

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.data.sources_catalog import LeagueMeta
from app.models.snapshot import Snapshot
from app.models.user import Subscription, User
from app.services.report_builder import build_user_weekly_report
from app.services.snapshots import get_latest_snapshot_payload
from tests.conftest import AsyncSessionTest


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _register_and_login(client: TestClient) -> Dict[str, str]:
    client.post(
        "/auth/register",
        json={"email": "snap@test.com", "password": "Passw0rd!", "language": "en"},
    )
    login = client.post(
        "/auth/login",
        json={"email": "snap@test.com", "password": "Passw0rd!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_scrape_run_persists_snapshot(client, monkeypatch):
    headers = _register_and_login(client)

    class DummyBundle:
        def __init__(self):
            self.meta = LeagueMeta("PL", "Premier League", "England", "premier-league")

    async def fake_fetch_bundle(code: str):
        assert code == "PL"
        return DummyBundle()

    class DummyNormalized:
        def __init__(self):
            self.payload = {
                "league_code": "PL",
                "league_name": "Premier League",
                "table": [],
                "fixtures_next": [],
                "top_scorers": [],
                "sources_used": ["https://example.com"],
            }
            self.sources = self.payload["sources_used"]

    def fake_bundle_to_facts(_bundle):
        return DummyNormalized()

    monkeypatch.setattr("app.api.scrape.fetch_league_bundle", fake_fetch_bundle)
    monkeypatch.setattr("app.api.scrape.bundle_to_facts", fake_bundle_to_facts)

    async def _count_snapshots():
        async with AsyncSessionTest() as session:
            res = await session.execute(select(Snapshot))
            return len(res.scalars().all())

    before = _run_async(_count_snapshots())

    resp = client.post("/scrape/run", json={"leagues": ["PL"]}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True

    latest = client.get("/facts/latest?league=PL", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["league_code"] == "PL"

    after = _run_async(_count_snapshots())
    assert after == before + 1


def test_build_report_prefers_snapshot(client, monkeypatch):
    async def seed():
        async with AsyncSessionTest() as session:
            user = User(email="snapshot-user@test.com", password_hash="hash", language="en")
            session.add(user)
            await session.flush()
            session.add(Subscription(user_id=user.id, league="PL", is_active=True))
            snapshot = Snapshot(
                user_id=user.id,
                league_code="PL",
                payload={
                    "league_code": "PL",
                    "league_name": "Premier League",
                    "table": [
                        {"rank": 1, "team": "Arsenal", "points": 25},
                    ],
                    "fixtures_next": [],
                    "top_scorers": [],
                    "sources_used": ["https://example.com"],
                },
            )
            session.add(snapshot)
            await session.commit()
            return str(user.id)

    user_id = _run_async(seed())

    async def snapshot_exists():
        async with AsyncSessionTest() as session:
            res = await session.execute(
                select(Snapshot).where(
                    Snapshot.user_id == user_id,
                    Snapshot.league_code == "PL",
                )
            )
            return res.scalars().first() is not None

    assert _run_async(snapshot_exists())

    async def ensure_helper():
        async with AsyncSessionTest() as session:
            return await get_latest_snapshot_payload(session, user_id, "PL")

    assert _run_async(ensure_helper()) is not None

    async def failing_fetch(_league):
        raise AssertionError("fetch_league_bundle should not be called when snapshot exists")

    monkeypatch.setattr("app.services.report_builder.fetch_league_bundle", failing_fetch)

    async def run_builder():
        async with AsyncSessionTest() as session:
            return await build_user_weekly_report(user_id, session)

    result = _run_async(run_builder())
    assert result["articles"], "Expected articles built from snapshot"
