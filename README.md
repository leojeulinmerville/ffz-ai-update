## Football Fan Zone – AI Weekly Companion

FFZ scrapes live BBC football data, snapshots it per league, feeds an LLM to write engaging stories, then formats and delivers them to each subscribed user via WhatsApp or Maileroo email. The pipeline is “agentic”: data acquisition, reasoning (LLM + guards), and delivery are separate agents orchestrated by the scheduler or the admin console.

---

### Stack at a Glance
- **FastAPI** – public/admin APIs and HTML console (`app/main.py`, `app/api/*`).
- **SQLite + Alembic** – persistence and migrations (`ffz.db`, `migrations/`).
- **Async SQLAlchemy** – DB access (`app/models/*`, `app/models/db.py`).
- **Scraping/normalization** – BBC standings/fixtures/scorers (`app/data/extractor/leagues.py`, `app/data/normalizer.py`).
- **LLM generation** – Mistral or OpenAI (`app/news/llm_generator.py`) guarded by `app/services/quality_guard.py`; falls back to deterministic copy if JSON is bad or providers fail.
- **Delivery** – WhatsApp/CallMeBot (`app/services/whatsapp_sender.py`) and Maileroo email (`app/services/email_sender.py`), channel-specific formatting in `app/services/formatter.py`.
- **Scheduler** – APScheduler + CLI runner (`app/scheduler/jobs.py`, `app/scheduler/weekly.py`).
- **Admin UI** – single-page console (`app/api/admin_page.py`, `app/static/admin.html`, `app/static/admin.js`).

Key flow:
1) Scrape/snapshot: fetch BBC data, normalize, and cache per league.
2) Build report: assemble user facts, call LLM (Mistral → OpenAI → fallback), parse JSON (code-fence tolerant), and guard output.
3) Deliver: format per channel, chunk WhatsApp, build HTML/plain email, send via provider, record status.
4) Orchestrate: scheduler runs weekly (Mon 09:00 Europe/Paris, or interval override) or via admin buttons; `/news/send_latest` delivers on demand.

---

### LLM Providers
- Order: Mistral (if `MISTRAL_API_KEY` set) → OpenAI (if `OPENAI_API_KEY` set) → deterministic fallback.
- Calls now include safe choice handling; JSON parsing tolerates code fences and logs non-JSON content.
- Adjust weights in `.env`: `MISTRAL_MODEL`, `OPENAI_MODEL`.

---

### Admin Console (http://localhost:8000/admin)
- Save user & leagues: POST `/admin/user` creates/updates the user, resets password to `changeme`, and returns an `access_token` (auto-stored by `admin.js`). Mandatory: at least one league.
- Followed leagues: dynamically fetched from `/meta/leagues`; favorite teams fetched from `/meta/leagues/{code}/teams`.
- Actions: Generate Weekly Report (calls `/news/generate`), Send Latest by Email (channel=email; WhatsApp available via API), delivery status shown in UI.
- Tip: If tokens get stale, clear browser localStorage and save again (password resets to `changeme` on save).

---

### Running the Stack
```bash
# Build & start
docker compose -f docker/docker-compose.yml up --build -d

# Apply migrations (run manually when models change)
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# Restart (clears schema guard, reloads scheduler)
docker compose -f docker/docker-compose.yml restart api

# Logs
docker compose -f docker/docker-compose.yml logs -f api
```
- Admin: http://localhost:8000/admin
- Health: http://localhost:8000/health (scheduler + DB readiness)

---

### Scheduler & Cron
- Auto-registered on startup; default: Mondays 09:00 Europe/Paris.
- Override cadence: `FFZ_SCHEDULER_INTERVAL_MINUTES=<int>`.
- Manual run: `docker compose -f docker/docker-compose.yml exec api python -m app.scheduler.weekly`
- Current behavior: generates reports for active subscribers; delivery remains operator-triggered via `/news/send_latest` (or extend scheduler to auto-send).

---

### Environment (.env)
```env
TZ=Europe/Paris
DATABASE_URL=sqlite+aiosqlite:////app/ffz.db
SECRET_KEY=<random>

MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-latest
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=mistral

WHATSAPP_PROVIDER=callmebot
WA_PHONE=+33600000000
WA_API_KEY=<callmebot-token>
WA_SENDER_NAME=FFZ-Agent

MAILEROO_API_KEY=...
MAILEROO_DEFAULT_FROM=no-reply@xxxx.maileroo.org
MAILEROO_FROM_NAME=Football Fan Zone
```

---

### Repo Map (high value)
| Path | Purpose |
| --- | --- |
| `app/api/admin_page.py` | Serves admin UI HTML and `/admin/user` upsert endpoint. |
| `app/static/admin.js` | Admin UX (save user/leagues, auto-login, generate/send actions). |
| `app/news/llm_generator.py` | LLM calls (Mistral/OpenAI), JSON parsing, provider order. |
| `app/services/formatter.py` | WhatsApp chunks + HTML/plain email bodies with fan summary. |
| `app/services/email_sender.py` | Maileroo integration. |
| `app/services/whatsapp_sender.py` | CallMeBot integration + chunking. |
| `app/services/quality_guard.py` | Validates/repairs LLM output; deterministic fallback. |
| `app/scheduler/jobs.py` | Registers weekly cron/interval jobs. |
| `migrations/` | Alembic migrations (run manually). |

---

### Tests
```bash
# inside Docker
docker compose -f docker/docker-compose.yml exec api python -m pytest -q

# or locally
pip install -r requirements.txt
python -m pytest -q
```
Key: `tests/test_send_latest.py` (delivery paths), `tests/scheduler/test_weekly_scheduler.py`.

---

### Troubleshooting
- Schema 503: `docker compose -f docker/docker-compose.yml exec api alembic upgrade head`, then restart API.
- 401 after save in admin: save again to reset password to `changeme` and refresh token; or clear localStorage.
- Mistral 429 / OpenAI errors: provider falls back; switch model/provider or throttle.
- WhatsApp skipped: ensure `WA_PHONE`/`WA_API_KEY` and CallMeBot registration.
- Maileroo skipped: check `MAILEROO_*` vars; logs show reference IDs on success.

---

### Agentic Notes
Data agent (scraper/normalizer) → Reasoning agent (LLM + guard) → Delivery agents (WhatsApp/Maileroo) → Orchestrator (scheduler/admin). Each stage is decoupled so failures in one fall back or retry without blocking the others.
