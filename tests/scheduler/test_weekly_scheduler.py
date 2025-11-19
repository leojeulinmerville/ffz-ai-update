import asyncio

import pytest

from app.scheduler import weekly
from app.models.user import User, Subscription
from tests.conftest import AsyncSessionTest, override_init_db


async def _create_user(email: str, *, subscribed: bool = True) -> str:
    async with AsyncSessionTest() as session:
        user = User(email=email, password_hash="hash", language="en", first_name="Test")
        session.add(user)
        await session.flush()
        if subscribed:
            session.add(
                Subscription(
                    user_id=user.id,
                    league="PL",
                    is_active=True,
                    frequency="weekly",
                )
            )
        await session.commit()
        return str(user.id)


@pytest.mark.usefixtures("event_loop")
def test_run_weekly_reports_happy_path(monkeypatch):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(override_init_db())

    processed = []

    async def fake_generate(user_id, session):
        processed.append(user_id)
        return {"email_status": {"success": True}}

    monkeypatch.setattr(
        "app.scheduler.weekly.generate_and_store_weekly_report",
        fake_generate,
    )

    subscribed_user = loop.run_until_complete(_create_user("subscribed@example.com"))
    loop.run_until_complete(_create_user("nosub@example.com", subscribed=False))

    summary = loop.run_until_complete(
        weekly.run_weekly_reports_for_all_users(session_factory=AsyncSessionTest)
    )

    assert summary["total_users"] == 1
    assert summary["success"] == 1
    assert summary["failed"] == 0
    assert processed == [subscribed_user]
    assert summary["results"][0]["email_status"] == {"success": True}


@pytest.mark.usefixtures("event_loop")
def test_run_weekly_reports_handles_exceptions(monkeypatch):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(override_init_db())

    async def fake_generate(user_id, session):
        if user_id == "fail":
            raise RuntimeError("boom")
        return {"email_status": {"success": True}}

    monkeypatch.setattr(
        "app.scheduler.weekly.generate_and_store_weekly_report",
        fake_generate,
    )

    ok_user_id = loop.run_until_complete(_create_user("ok@example.com"))
    failing_user_id = loop.run_until_complete(_create_user("fail@example.com"))

    # force failing user id to known value
    async def _patch_id():
        async with AsyncSessionTest() as session:
            user = await session.get(User, failing_user_id)
            user.id = "fail"
            await session.commit()
        return "fail"

    loop.run_until_complete(_patch_id())

    summary = loop.run_until_complete(
        weekly.run_weekly_reports_for_all_users(session_factory=AsyncSessionTest)
    )

    assert summary["total_users"] == 2
    assert summary["success"] == 1
    assert summary["failed"] == 1

    ok_entry = next(item for item in summary["results"] if item["email"] == "ok@example.com")
    fail_entry = next(item for item in summary["results"] if item["email"] == "fail@example.com")

    assert ok_entry["ok"] is True
    assert fail_entry["ok"] is False
    assert "boom" in fail_entry["error"]


@pytest.mark.usefixtures("event_loop")
def test_cli_main_prints_summary(monkeypatch, capsys):
    async def fake_run(**_):
        return {"total_users": 5, "success": 5, "failed": 0, "results": []}

    monkeypatch.setattr("app.scheduler.weekly.run_weekly_reports_for_all_users", fake_run)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(weekly.main())

    captured = capsys.readouterr()
    assert "5/5" in captured.out
