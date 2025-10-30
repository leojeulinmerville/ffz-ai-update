import httpx

API_URL = "https://api.football-data.org/v4/competitions"
API_KEY = "YOUR_API_KEY"  # ⚠️ À mettre dans ton .env

async def fetch_league_standings(league_code: str):
    """Retourne le classement de la ligue demandée."""
    url = f"{API_URL}/{league_code}/standings"
    headers = {"X-Auth-Token": API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"API returned {response.status_code}"}
        data = response.json()
        table = data.get("standings", [])[0].get("table", [])
        return [{"team": t["team"]["name"], "points": t["points"]} for t in table]
