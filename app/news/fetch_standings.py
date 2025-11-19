# app/news/fetcher.py

import os
import httpx

API_URL = "https://api.football-data.org/v4/competitions"
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")  # mets ça dans .env

async def fetch_league_standings(league_code: str):
    """
    Retourne une liste normalisée:
    [
      {"rank": 1, "team": "PSG", "pts": 27},
      {"rank": 2, "team": "Monaco", "pts": 25},
      ...
    ]

    En dev, si pas d'API_KEY -> on renvoie du mock.
    """

    # MODE MOCK (développement sans clé)
    if not API_KEY:
        dummy = {
            "FRA1": [
                {"rank": 1, "team": "PSG", "pts": 27},
                {"rank": 2, "team": "Monaco", "pts": 25},
                {"rank": 3, "team": "Nice", "pts": 24},
                {"rank": 4, "team": "Lyon", "pts": 21},
                {"rank": 5, "team": "Lille", "pts": 20},
            ],
            "ENG1": [
                {"rank": 1, "team": "Manchester City", "pts": 30},
                {"rank": 2, "team": "Liverpool", "pts": 28},
                {"rank": 3, "team": "Arsenal", "pts": 26},
                {"rank": 4, "team": "Tottenham", "pts": 23},
                {"rank": 5, "team": "Aston Villa", "pts": 22},
            ],
        }
        return dummy.get(league_code, [])

    # MODE LIVE
    url = f"{API_URL}/{league_code}/standings"
    headers = {"X-Auth-Token": API_KEY}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code != 200:
        return []

    data = resp.json()
    # on va chercher le 1er classement (généralement "TOTAL")
    table = (data.get("standings") or [{}])[0].get("table") or []

    normalized = []
    for row in table:
        normalized.append({
            "rank": row.get("position"),
            "team": row.get("team", {}).get("name"),
            "pts": row.get("points"),
        })

    return normalized
