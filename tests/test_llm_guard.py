from app.services import quality_guard


def test_quality_guard_normalizes_article_and_watchlist():
    facts = {
        "league_code": "PL",
        "league_name": "Premier League",
        "season_current": True,
        "top5": [
            {"club": "Arsenal", "points": 30},
            {"club": "Manchester City", "points": 29},
            {"club": "Liverpool", "points": 27},
            {"club": "Tottenham", "points": 25},
            {"club": "Aston Villa", "points": 21},
        ],
        "top_scorers": [
            {"player": "Bukayo Saka", "club": "Arsenal", "goals": 7},
            {"player": "Erling Haaland", "club": "Manchester City", "goals": 9},
        ],
        "tight_gaps": [{"pos1": 1, "pos2": 2, "gap_points": 1}],
        "top5_duels_this_week": [
            {"home": "Arsenal", "away": "Liverpool", "date_utc": "2025-03-15T17:30:00Z"},
        ],
        "calendar_notes": [],
        "fan_team": "Arsenal",
        "fan_form": ["W", "D", "W"],
        "next_match": {"home": "Arsenal", "away": "Liverpool", "utc_kickoff": "2025-03-15T17:30:00Z"},
        "source_timestamps": {"standings": "2025-03-10T12:00:00Z"},
    }

    candidate = {
        "league_code": "PL",
        "headline": "**Arsenal** stay hot",
        "narrative": "Arsenal keep the pace at the top while City chase closely. Watch the midweek clash!",
        "watchlist": ["- fake item", "- another markdown item"],
        "fan_spotlight": "*Arsenal* supporters can dream again.",
    }

    article, used_fallback = quality_guard.ensure_article(facts, candidate, "en", fan_focus=True)

    assert article["headline"]
    assert "*" not in article["headline"]
    assert len(article["watchlist"]) == 2
    assert all("*" not in item for item in article["watchlist"])
    assert article["fan_spotlight"] is None or "*" not in article["fan_spotlight"]
