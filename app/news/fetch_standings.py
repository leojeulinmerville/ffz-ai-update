# app/news/fetch_standings.py
"""
Fetch football standings (mocked or live later).
This version provides a textual summary for the LLM.
"""

import httpx

async def get_league_table(league_code: str) -> dict:
    """
    Returns data like:
    {
        "league_name": "Ligue 1",
        "table": "1. PSG - 27 pts\n2. Monaco - 25 pts\n3. Nice - 24 pts\n4. Lyon - 21 pts\n5. Lille - 20 pts"
    }
    """
    # TODO: replace this with a real API or scraper later
    dummy_tables = {
        "FRA1": {
            "league_name": "Ligue 1",
            "table": "1. PSG - 27 pts\n2. Monaco - 25 pts\n3. Nice - 24 pts\n4. Lyon - 21 pts\n5. Lille - 20 pts"
        },
        "ENG1": {
            "league_name": "Premier League",
            "table": "1. Manchester City - 30 pts\n2. Liverpool - 28 pts\n3. Arsenal - 26 pts\n4. Tottenham - 23 pts\n5. Aston Villa - 22 pts"
        }
    }

    return dummy_tables.get(league_code, {
        "league_name": league_code,
        "table": "No data available"
    })
