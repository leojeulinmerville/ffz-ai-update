import asyncio
import json
def test_send_latest_updates_delivery(client, monkeypatch):
    async def fake_send(_payload):
        return {
            "status": "sent",
            "parts": [{"part": 1, "ok": True, "info": "HTTP 200"}],
            "sent_at": "2025-01-01T00:00:00",
        }

    monkeypatch.setattr("app.api.news.send_weekly_report_via_whatsapp", fake_send)

    from sqlalchemy import select
    from app.models.user import User
    from app.models.weekly_report import WeeklyReport
    from tests.conftest import AsyncSessionTest

    register_payload = {
        "email": "sendlatest@example.com",
        "password": "Passw0rd!",
        "language": "en",
    }
    resp = client.post("/auth/register", json=register_payload)
    assert resp.status_code == 200

    login_resp = client.post("/auth/login", json={"email": "sendlatest@example.com", "password": "Passw0rd!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async def insert_report() -> str:
        async with AsyncSessionTest() as session:
            user_result = await session.execute(
                select(User).where(User.email == "sendlatest@example.com")
            )
            user = user_result.scalars().first()
            article_text = (
                "Premier League — Weekly snapshot\n"
                "\n"
                "Top five:\n"
                "1. Arsenal (30 pts)\n"
                "\n"
                "Trend: Solid run.\n"
                "\n"
                "Watchlist:\n"
                "- Top scorer to watch."
            )

            report = WeeklyReport(
                user_id=user.id,
                language="en",
                payload=json.dumps(
                    {
                        "user": {"email": user.email, "language": "en", "favorite_team": None},
                        "articles": [
                            {
                                "league_code": "ENG1",
                                "league_name": "Premier League",
                                "text": article_text,
                                "generator_provider": "fallback",
                            }
                        ],
                    }
                ),
                delivery_status="generated",
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report.id
    report_id = asyncio.run(insert_report())

    latest_check = client.get("/news/latest", headers=headers)
    assert latest_check.status_code == 200, latest_check.text

    send_resp = client.post("/news/send_latest", headers=headers)
    assert send_resp.status_code == 200, send_resp.text
    data = send_resp.json()
    assert data["status"] == "sent"
    assert data["parts"][0]["ok"] is True
    assert data["channel"] == "whatsapp"

    async def fetch_report():
        async with AsyncSessionTest() as session:
            res = await session.execute(
                select(WeeklyReport).where(WeeklyReport.id == report_id)
            )
            return res.scalars().first()

    latest = asyncio.run(fetch_report())
    assert latest.delivery_status == "sent"
    assert latest.delivery_channel == "whatsapp"
    assert latest.delivered_at is not None


def test_send_latest_via_email(client, monkeypatch):
    async def fake_email_send(_payload, email, name=None):
        return {
            "status": "sent",
            "reference_id": "msg-123",
            "sent_at": "2025-01-01T00:00:00",
        }

    async def fake_whatsapp(_payload):
        raise AssertionError("WhatsApp should not be invoked when channel=email")

    monkeypatch.setattr("app.api.news.send_weekly_report_via_email", fake_email_send)
    monkeypatch.setattr("app.api.news.send_weekly_report_via_whatsapp", fake_whatsapp)

    from sqlalchemy import select
    from app.models.user import User
    from app.models.weekly_report import WeeklyReport
    from tests.conftest import AsyncSessionTest

    register_payload = {
        "email": "sendemail@example.com",
        "password": "Passw0rd!",
        "language": "fr",
    }
    resp = client.post("/auth/register", json=register_payload)
    assert resp.status_code == 200

    login_resp = client.post("/auth/login", json={"email": "sendemail@example.com", "password": "Passw0rd!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async def insert_report() -> str:
        async with AsyncSessionTest() as session:
            user_result = await session.execute(
                select(User).where(User.email == "sendemail@example.com")
            )
            user = user_result.scalars().first()
            report = WeeklyReport(
                user_id=user.id,
                language="fr",
                payload=json.dumps(
                    {
                        "user": {"email": user.email, "language": "fr", "favorite_team": "OM"},
                        "articles": [
                            {
                                "league_code": "FR1",
                                "league_name": "Ligue 1",
                                "narrative": "Victoire convaincante.",
                                "watchlist": ["Suivre la défense."],
                                "fan_spotlight": "Les supporters ont été incroyables.",
                                "generator_provider": "fallback",
                            }
                        ],
                    }
                ),
                delivery_status="generated",
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report.id

    report_id = asyncio.run(insert_report())

    send_resp = client.post("/news/send_latest", headers=headers, json={"channel": "email"})
    assert send_resp.status_code == 200, send_resp.text
    data = send_resp.json()
    assert data["status"] == "sent"
    assert data["channel"] == "email"
    assert data["reference_id"] == "msg-123"

    async def fetch_report():
        async with AsyncSessionTest() as session:
            res = await session.execute(
                select(WeeklyReport).where(WeeklyReport.id == report_id)
            )
            return res.scalars().first()

    latest = asyncio.run(fetch_report())
    assert latest.delivery_status == "sent"
    assert latest.delivery_channel == "email"
    assert latest.delivered_at is not None
