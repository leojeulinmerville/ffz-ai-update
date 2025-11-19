from app.services.email_formatter import format_weekly_report_email


def _base_payload():
    return {
        "user": {
            "email": "fan@example.com",
            "language": "en",
            "favorite_team": "Arsenal",
            "first_name": "Alex",
            "last_name": "Doe",
        },
        "articles": [],
        "health": {"status": "ok"},
    }


def test_email_formatter_with_articles():
    payload = _base_payload()
    payload["articles"] = [
        {
            "league_name": "Premier League",
            "headline": "Arsenal keep the pace",
            "narrative": "Arsenal continue to lead after a disciplined win.",
            "watchlist": ["Mind the gap with City.", "Focus on midweek rotation."],
        },
        {
            "league_name": "Ligue 1",
            "headline": "Nice stay in the hunt",
            "narrative": "OGC Nice push PSG thanks to another strong defensive outing.",
            "watchlist": ["Next test vs Metz."],
        },
    ]

    subject, text_body, html_body = format_weekly_report_email(payload)
    assert "Arsenal" in subject
    assert text_body.startswith("Hi Alex,")
    assert "=== Premier League ===" in text_body
    assert "Watchlist:" in text_body
    assert "<h2>Premier League</h2>" in html_body
    assert "<ul><li>Mind the gap with City.</li><li>Focus on midweek rotation.</li></ul>" in html_body


def test_email_formatter_no_articles():
    payload = _base_payload()
    payload["articles"] = []

    subject, text_body, html_body = format_weekly_report_email(payload)
    assert subject == "Your Football Fan Zone weekly report – Arsenal"
    assert "No leagues to report this week" in text_body
    assert "No leagues to report this week" in html_body


def test_email_formatter_minimal_user():
    payload = {
        "user": {
            "email": "fan@example.com",
            "language": "en",
            "favorite_team": None,
        },
        "articles": [
            {
                "league_name": "Bundesliga",
                "narrative": "Dortmund climb to second place.",
                "watchlist": [],
            }
        ],
    }

    subject, text_body, _ = format_weekly_report_email(payload)
    assert subject == "Your Football Fan Zone weekly report"
    assert text_body.startswith("Hi,")
