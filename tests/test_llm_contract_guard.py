from app.services import quality_guard


def _base_facts():
    return {
        "league_code": "PL",
        "league_name": "Premier League",
        "fan_team": "Arsenal",
        "top5": [
            {"club": "Arsenal", "points": 26, "rank": 1},
            {"club": "Manchester City", "points": 24, "rank": 2},
            {"club": "Chelsea", "points": 23, "rank": 3},
            {"club": "Liverpool", "points": 22, "rank": 4},
            {"club": "Tottenham", "points": 21, "rank": 5},
        ],
        "table": [
            {"team": "Arsenal", "points": 26, "rank": 1},
            {"team": "Manchester City", "points": 24, "rank": 2},
            {"team": "Chelsea", "points": 23, "rank": 3},
            {"team": "Liverpool", "points": 22, "rank": 4},
            {"team": "Tottenham", "points": 21, "rank": 5},
        ],
        "tight_gaps": [
            {"pos1": 1, "pos2": 2, "gap_points": 2},
        ],
        "top_scorers": [
            {"player": "E. Haaland", "club": "Man City", "goals": 14},
            {"player": "I. Thiago", "club": "Brentford", "goals": 8},
        ],
        "next_match": {
            "home": "Arsenal",
            "away": "Chelsea",
            "local_kickoff": "2025-11-20T18:00:00+01:00",
        },
        "sources_used": [
            "https://www.bbc.com/sport/football/premier-league/table",
            "https://www.bbc.com/sport/football/premier-league/scores-fixtures",
            "https://www.bbc.com/sport/football/premier-league/top-scorers",
        ],
    }


def test_watchlist_and_sources_trimmed():
    facts = _base_facts()
    candidate = {
        "league_code": "PL",
        "headline": "Arsenal keep the pace",
        "narrative": "Arsenal remain in control at the top with Manchester City two points back and Chelsea pressing the duo. The race stays tense heading into the weekend fixtures.",
        "watchlist": [
            "Keep an eye on Havertz.",
            "City play twice this week.",
            "Extra bullet that should be dropped.",
        ],
        "fan_spotlight": "Stay alert for the Chelsea press on Sunday night.",
    }

    article, fallback_used = quality_guard.ensure_article(facts, candidate, "en", fan_focus=True)

    assert len(article["watchlist"]) == 2
    assert all(len(item) <= 80 for item in article["watchlist"])
    assert article["fan_spotlight"] is not None
    assert fallback_used  # watchlist trimmed triggers regeneration flag


def test_narrative_too_short_triggers_regen():
    facts = _base_facts()
    candidate = {
        "league_code": "PL",
        "headline": "Arsenal stay top",
        "narrative": "Short line.",
        "watchlist": ["Mind the gap.", "Next match decides it."],
        "fan_spotlight": "Fans stay calm.",
    }

    article, fallback_used = quality_guard.ensure_article(facts, candidate, "en", fan_focus=True)

    assert len(article["narrative"]) >= 350
    assert fallback_used
    assert article["fan_spotlight"] is not None
