from app.services.formatter import format_weekly_report_text


def _build_article(code: str, narrative: str, fan_spotlight: str | None) -> dict:
    return {
        "league_code": code,
        "league_name": "Premier League" if code == "PL" else "Ligue 1",
        "headline": f"{code} headline",
        "narrative": narrative,
        "fan_spotlight": fan_spotlight,
        "watchlist": ["Only 2 points separate City and Chelsea.", "Monitor weekend line-ups for late changes."],
        "sources_used": [
            f"https://www.bbc.com/sport/football/{'premier-league' if code == 'PL' else 'french-ligue-one'}/table",
            f"https://www.bbc.com/sport/football/{'premier-league' if code == 'PL' else 'french-ligue-one'}/scores-fixtures",
            f"https://www.bbc.com/sport/football/{'premier-league' if code == 'PL' else 'french-ligue-one'}/top-scorers",
        ],
        "facts": {"fan_team": "Arsenal" if fan_spotlight else None},
    }


def test_formatter_builds_chunked_payload():
    payload = {
        "user": {"language": "en", "favorite_team": "Arsenal"},
        "articles": [
            _build_article(
                "PL",
                narrative="Arsenal sit on 26 points while Manchester City chase at 22, with Chelsea and Spurs clustered closely behind ahead of the weekend slate.",
                fan_spotlight="Your next match against Chelsea demands patience: protect the half-spaces, recycle possession, and trust the front line to convert.",
            ),
            _build_article(
                "FL1",
                narrative="Paris stay in control on 27 points but Marseille and Lens remain within two points, keeping the title race alive heading into December.",
                fan_spotlight=None,
            ),
        ],
    }

    chunks = format_weekly_report_text(payload)

    assert chunks[0].startswith("Football Fan Zone — Your weekly update")
    assert chunks[-1] == "See you next week. ⚽️ FFZ"
    assert any("Fan Spotlight —" in chunk for chunk in chunks)
    assert sum("Watchlist:" in chunk for chunk in chunks) == 2
    assert all(len(chunk) <= 950 for chunk in chunks)
    league_chunks = [chunk for chunk in chunks if chunk.startswith("PL headline") or chunk.startswith("FL1 headline")]
    assert len(league_chunks) == 2
    assert all("• Only 2 points separate City and Chelsea." in chunk for chunk in league_chunks)
    assert all("Sources: BBC table / fixtures / scorers" in chunk for chunk in league_chunks)
