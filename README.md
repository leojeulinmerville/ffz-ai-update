## Football Fan Zone – Micro Scrape Preview

This micro‑MVP exposes live BBC data (standings, fixtures, top scorers) without touching the database.  
It powers the `/admin` console so you can preview real content before rolling out full persistence.

---

### 1. Prerequisites

- Python 3.12 (optional, only for local tooling/tests)
- Docker Desktop
- `.env` file at repo root (defaults shown below):

```env
TZ=Europe/Paris
DATABASE_URL=sqlite+aiosqlite:///./ffz.db
SCRAPE_TIME_WINDOW_DAYS=45
CACHE_TTL_SECONDS=7200
ALLOWED_DOMAINS=uefa.com,ligue1.com,premierleague.com,bundesliga.com,laliga.com,legaseriea.it,bbc.com,lequipe.fr,fbref.com,understat.com,transfermarkt.com
USE_PLAYWRIGHT=false
PROXY_URL=
SECRET_KEY=devsecret
```

---

### 2. Build & Run

```bash
# stop previous stack
docker compose -f docker/docker-compose.yml down -v

# build and start the API
docker compose -f docker/docker-compose.yml up --build -d

# apply database migrations (required the first time)
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# tail logs
docker compose -f docker/docker-compose.yml logs -f api

# open the admin console
open http://localhost:8000/admin   # (use xdg-open/start on Linux/Windows)
```

> If `/news/generate` returns `500` mentioning `no such column`, rerun `alembic upgrade head` as above.

---

### 3. Live Endpoints

All endpoints fetch BBC pages on demand, cached in-memory for 2 hours.

```bash
# list supported leagues (PL, FL1, PD, BL1, SA, CL)
curl http://localhost:8000/meta/leagues

# fetch the teams for Ligue 1 (derived from standings)
curl http://localhost:8000/meta/leagues/FL1/teams

# preview a league scrape (BBC standings + fixtures + top scorers)
curl "http://localhost:8000/scrape/preview?league=FL1"
```

Response example for `/scrape/preview`:

```json
{
  "league_code": "FL1",
  "league_name": "Ligue 1",
  "table": [ { "rank": 1, "team": "OGC Nice", "points": 20, ... } ],
  "fixtures_next": [ { "home": "Metz", "away": "Nice", "kickoff_utc": "2025-11-10T15:00:00Z" } ],
  "top_scorers": [ { "player": "Mbappé", "team": "Paris SG", "goals": 9 } ],
  "sources_used": [
    "https://www.bbc.com/sport/football/french-ligue-one/table",
    "https://www.bbc.com/sport/football/french-ligue-one/scores-fixtures",
    "https://www.bbc.com/sport/football/french-ligue-one/top-scorers"
  ]
}
```

The `/admin` page now uses these endpoints:

- “Reload leagues” → `/meta/leagues`
- “Favorite team” dropdown → `/meta/leagues/{code}/teams`
- “Scrape now (preview)” → `/scrape/preview?league=<selected>` (output shown in “Latest payload” panel)

---

### 4. Snapshot Lite (persisted facts)

Use the lightweight snapshot flow to store one payload per user+league:

```bash
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# run once to persist a snapshot for a league
curl -H "Authorization: Bearer <JWT>" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8000/scrape/run \
     -d '{"leagues":["FL1"]}'

# reuse it
curl -H "Authorization: Bearer <JWT>" \
     "http://localhost:8000/facts/latest?league=FL1"
```

`/news/generate` now prefers the latest snapshot for each followed league, falling back to a fresh scrape only when none exists (and writing a snapshot immediately).

---

### 5. WhatsApp formatting rules

- Messages are chunked at 950 characters maximum (intro + per-league chunk + optional fan chunk + outro).
- Each league chunk contains: headline, 450-700 character narrative, Watchlist: header plus exactly two ? bullet lines, and a footer Sources: BBC table / fixtures / scorers.
- Fan spotlight appears as its own chunk (Fan Spotlight -- <team>) only if the favourite club has an upcoming fixture.
- Intro chunk: Football Fan Zone -- Your weekly update. (language-specific). Outro chunk: See you next week. ?? FFZ.

### 6. Tests

Unit tests run entirely offline using recorded fixtures.

`ash
# inside Docker (recommended)
docker compose -f docker/docker-compose.yml run --rm api python -m pytest -q

# or locally (after pip install -r requirements.txt)
python -m pytest -q
`

Included test: 	ests/test_extractor_leagues.py validates the BBC standings parser against an HTML fixture.

---

### 7. Respect Robots & Sources

- All HTTP calls respect 
obots.txt and the domain allowlist.
- If a domain disallows scraping, the API returns 403.
- Every payload includes sources_used so downstream consumers can cite BBC properly.

**Troubleshooting**

- /scrape/preview -> 403: BBC's robots.txt forbids that path. Switch leagues or wait for allowance.
- /scrape/preview -> 502: transient network error; retry after a few seconds and confirm the domain remains on the allowlist.

Enjoy previewing real Ligue 1 / Premier League data in /admin!  
Next steps (outside this micro-MVP) will wire these facts into persistent jobs and the LLM writer.
