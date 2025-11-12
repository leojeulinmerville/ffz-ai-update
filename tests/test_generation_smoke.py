import asyncio
import json
from sqlalchemy import select

from tests.conftest import AsyncSessionTest


def test_generate_and_store_weekly_report(monkeypatch):
    from app.models.user import User, Subscription
    from app.models.weekly_report import WeeklyReport
    from app.services.generation_service import generate_and_store_weekly_report
    from app.data.sources_catalog import LeagueMeta
    from app.data.extractor.leagues import LeagueBundle, StandingRow, FixtureRow, ScorerRow
    from app.data.normalizer import NormalizedFacts

    dummy_bundle = LeagueBundle(
        meta=LeagueMeta("PL", "Premier League", "England", "premier-league"),
        standings=[
            StandingRow(rank=1, team="Arsenal", played=10, wins=8, draws=1, losses=1, goals_for=25, goals_against=8, points=25)
        ],
        fixtures=[
            FixtureRow(home="Arsenal", away="Chelsea", kickoff_local=None, kickoff_utc=None)
        ],
        top_scorers=[ScorerRow(player="Bukayo Saka", team="Arsenal", goals=7)],
    )

    async def fake_fetch_bundle(code: str):
        return dummy_bundle

    def fake_bundle_to_facts(_bundle):
        payload = {
            "league_code": "PL",
            "league_name": "Premier League",
            "table": [
                {"rank": 1, "team": "Arsenal", "played": 10, "wins": 8, "draws": 1, "losses": 1, "goals_for": 25, "goals_against": 8, "points": 25}
            ],
            "fixtures_next": [
                {"home": "Arsenal", "away": "Chelsea", "kickoff_local": None, "kickoff_utc": None}
            ],
            "top_scorers": [
                {"player": "Bukayo Saka", "team": "Arsenal", "goals": 7}
            ],
            "sources_used": ["https://example.com/table", "https://example.com/fixtures", "https://example.com/scorers"],
        }
        return NormalizedFacts(facts=[], payload=payload, sources=payload["sources_used"])

    monkeypatch.setattr("app.services.report_builder.fetch_league_bundle", fake_fetch_bundle)
    monkeypatch.setattr("app.services.report_builder.bundle_to_facts", fake_bundle_to_facts)

    async def _prepare():
        async with AsyncSessionTest() as session:
            user = User(email="smoke@example.com", password_hash="hash", language="en")
            session.add(user)
            await session.flush()
            session.add(Subscription(user_id=user.id, league="PL", is_active=True))
            await session.commit()
            return user.id

    loop = asyncio.new_event_loop()
    try:
        user_id = loop.run_until_complete(_prepare())
    finally:
        loop.close()

    async def _generate():
        async with AsyncSessionTest() as session:
            result = await generate_and_store_weekly_report(user_id, session)
            assert result["report"]["articles"], "expected generated articles"
            stmt = select(WeeklyReport).where(WeeklyReport.user_id == user_id)
            db_result = await session.execute(stmt)
            report = db_result.scalars().first()
            assert report is not None
            payload = json.loads(report.payload)
            assert payload["articles"], "stored payload missing articles"

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_generate())
    finally:
        loop.close()
