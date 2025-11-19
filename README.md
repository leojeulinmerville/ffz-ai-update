## Football Fan Zone – AI Weekly Companion

Football Fan Zone (FFZ) aggregates live BBC football data, snapshots it per league, lets an LLM craft tailored stories, and delivers the result to every subscribed user. The system behaves like an “agentic AI” pipeline: one job gathers structured facts, a second agent (the LLM writer) reasons over those facts to generate narratives, and delivery agents format/send the stories through WhatsApp or Maileroo email.

---

### Stack at a Glance

- **FastAPI** – public/admin APIs and HTML console (`app/main.py`, `app/api/*`).
- **SQLite + Alembic** – lightweight persistence (`ffz.db`, `migrations/`).
- **Async SQLAlchemy** – DB access (`app/models/*`, `app/models/db.py`).
- **Crawler layer** – BBC scrapers (`app/data/extractor/leagues.py`) + normalizer.
- **LLM agents** – `app/news/llm_generator.py` with Mistral/OpenAI, guarded by `app/services/quality_guard.py`.
- **Delivery agents** – WhatsApp via CallMeBot (`app/services/whatsapp_sender.py`) and Maileroo email (`app/services/email_sender.py`).
- **Scheduler** – APScheduler inside the API plus CLI runner (`app/scheduler/jobs.py`, `app/scheduler/weekly.py`). Automatically starts on API startup with robust error handling.
- **Admin UI** – one-page console (`app/api/admin_page.py`, `app/static/admin.js`).
- **Health Check** – `/health` endpoint for monitoring and platform health checks.
- **Auto-Migrations** – Database migrations run automatically on startup if needed.

Key agentic steps:
1. `scrape.run` routes fetch BBC standings/fixtures/scorers (respect robots + allowlist) and cache snapshots.
2. `report_builder` assembles per-user facts, calls the LLM, and falls back to deterministic copy if the model throttles (429, etc.).
3. Delivery agents format multi-channel content, chunk WhatsApp, or assemble long-form HTML/plain emails.
4. The scheduler orchestrates generation for all active users; operators fire `/news/send_latest` to push WhatsApp/email, or integrate mailing into cron later.
5. **Auto-startup** – Migrations execute automatically on container start, scheduler starts autonomously even if DB is temporarily unavailable.

---

### Repo Map

| Path | Purpose |
| --- | --- |
| `app/api/*.py` | HTTP routers: auth, news, admin page, scraping, subscriptions. |
| `app/data/extractor/leagues.py` | BBC parsing logic (standings, fixtures, scorers). |
| `app/news/llm_generator.py` | LLM wrapper (Mistral/OpenAI). |
| `app/services/formatter.py` | Channel-specific formatting (WhatsApp chunks + email bodies). |
| `app/services/email_sender.py` / `whatsapp_sender.py` | Delivery integrations (Maileroo & CallMeBot). |
| `app/scheduler/jobs.py` | APScheduler registration (weekly Mondays 09:00 Europe/Paris). Auto-starts with robust error handling. |
| `app/scheduler/weekly.py` | CLI scheduler runner for cron/manual triggers. |
| `app/models/*` | SQLAlchemy models (`User`, `Subscription`, `Snapshot`, `WeeklyReport`). |
| `migrations/` | Alembic migrations (run automatically on startup, or manually via `alembic upgrade head`). |
| `docker/docker-compose.yml` & `docker/Dockerfile` | Runtime packaging. Supports dynamic PORT for Railway/cloud platforms. |
| `railway.json` | Railway.app deployment configuration. |

---

### Installation & Environment

1. **Prerequisites**
   - Docker Desktop (or compatible engine).  
   - Optional: Python 3.12 + `pip install -r requirements.txt` for local tooling/tests.

2. **Environment**
   - Copy `.env.example` → `.env` (values shown below). Keep secrets local.

```env
TZ=Europe/Paris
DATABASE_URL=sqlite+aiosqlite:////app/ffz.db
SECRET_KEY=<random>

# LLM providers
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-latest
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=mistral

# WhatsApp (CallMeBot)
WHATSAPP_PROVIDER=callmebot
WA_PHONE=+33600000000
WA_API_KEY=<callmebot-token>
WA_SENDER_NAME=FFZ-Agent

# Maileroo
MAILEROO_API_KEY=...
MAILEROO_DEFAULT_FROM=no-reply@xxxx.maileroo.org
MAILEROO_FROM_NAME=Football Fan Zone
```

---

### Running the Stack

```bash
# Build & start API (daemonized)
docker compose -f docker/docker-compose.yml up --build -d

# Migrations run automatically on startup, but you can also run manually:
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# Restart to clear schema guard / reload scheduler
docker compose -f docker/docker-compose.yml restart api

# Tail logs
docker compose -f docker/docker-compose.yml logs -f api

# Check health status
curl http://localhost:8000/health
```

- Admin console: `http://localhost:8000/admin`
  - Register/login, follow leagues, run `Scrape preview`, `Run scrape job`, `Generate weekly report`.
  - Choose delivery channel (WhatsApp or Email) before pressing "Send latest report."
- Health endpoint: `http://localhost:8000/health`
  - Returns scheduler status and database readiness for monitoring.

---

### Scheduler & Cron

- APScheduler registers on API startup (`schedule_jobs`) and **starts automatically**.  
  - Default cadence: every Monday 09:00 Europe/Paris.  
  - Override with `FFZ_SCHEDULER_INTERVAL_MINUTES=<int>` for faster loops.
  - **Autonomous operation**: Scheduler starts even if database is temporarily unavailable, with robust error handling that retries on next scheduled run.
  - **No manual intervention required**: The scheduler runs continuously once the API starts.
- Manual run (inside container) - optional, for testing:

```bash
docker compose -f docker/docker-compose.yml exec api python -m app.scheduler.weekly
```

This walks every subscribed user, runs `generate_and_store_weekly_report`, and prints a summary (`success/failed`). Delivery (WhatsApp/email) still happens via `/news/send_latest` so operators can pick the channel per user; extend the scheduler if you want auto-send after generation.

---

### Deployment on Railway.app

FFZ is configured for easy deployment on Railway.app with automatic migrations and scheduler startup.

**Quick Deploy:**

1. Create account at [railway.app](https://railway.app)
2. New Project → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect `railway.json` and `docker/Dockerfile`
5. Add environment variables in Railway dashboard:
   - `SECRET_KEY` (generate a random string)
   - `MISTRAL_API_KEY` or `OPENAI_API_KEY`
   - `LLM_PROVIDER` (mistral or openai)
   - `WHATSAPP_PROVIDER`, `WA_PHONE`, `WA_API_KEY`
   - `MAILEROO_API_KEY`, `MAILEROO_DEFAULT_FROM`
   - `TZ=Europe/Paris`
   - `DATABASE_URL=sqlite+aiosqlite:////app/ffz.db`
6. Railway will automatically:
   - Build and deploy the container
   - Run migrations on startup (if needed)
   - Start the scheduler automatically
   - Provide a public URL

**Features:**
- ✅ Automatic migrations on startup
- ✅ Scheduler starts autonomously
- ✅ Health check endpoint at `/health`
- ✅ Dynamic PORT support (Railway sets `PORT` automatically)
- ✅ Persistent SQLite database via Railway volumes

**Note:** The scheduler requires the application to stay running 24/7. Railway's free tier provides 500 hours/month, which is sufficient for continuous operation.

---

### Tests

```bash
# inside Docker
docker compose -f docker/docker-compose.yml exec api python -m pytest -q

# or locally
pip install -r requirements.txt
python -m pytest -q
```

`tests/scheduler/test_weekly_scheduler.py` covers the scheduler orchestration; `tests/test_send_latest.py` ensures both WhatsApp and email delivery paths update DB metadata. Add fixtures under `tests/data/` if you capture new BBC HTML.

---

### Troubleshooting

- **Schema guard 503** – Migrations should run automatically on startup. If you see this error, migrations may have failed. Check logs, then run manually: `docker compose -f docker/docker-compose.yml exec api alembic upgrade head`, then restart the API.
- **`sqlite3.OperationalError: table X already exists`** – Delete/rename `ffz.db`, rerun migrations.
- **Scheduler not running** – Check `/health` endpoint. If `scheduler_running: false`, check logs for errors. The scheduler should start automatically on API startup.
- **Scheduler fails silently** – The scheduler has robust error handling and will retry on the next scheduled run. Check logs for details. If database is unavailable, scheduler will wait and retry automatically.
- **Mistral 429 (tier capacity)** – The agent falls back to deterministic copy (`quality_guard`). Switch LLM provider or throttle usage to avoid repeated fallbacks.
- **WhatsApp skipped** – Ensure `.env` has `WA_PHONE` & `WA_API_KEY`, and that the phone is registered with CallMeBot.
- **Maileroo skipped** – Check `MAILEROO_API_KEY` and default sender fields. Logs show reference IDs for successful sends.
- **Admin send button disabled** – You must `Generate weekly report` first (per-user cache). Use `Show latest report` to confirm payload before sending.
- **Railway deployment issues** – Ensure all environment variables are set. Check Railway logs. The `/health` endpoint helps verify scheduler and database status.

---

### Why “Agentic”?

Each stage is autonomous yet coordinated:

1. **Data agent** – Scraper/normalizer fetches live standings + fixtures + scorers, respects robots/allowlist, and snapshots results.
2. **Reasoning agent** – `report_builder` composes facts into prompts, lets the LLM plan narratives, and cross-checks with `quality_guard`.
3. **Delivery agents** – WhatsApp chunker enforces message limits, Maileroo builds HTML/plain text, both record status per user.
4. **Orchestrator** – APScheduler starts automatically on API startup and runs autonomously. It handles errors gracefully and retries on the next scheduled run. CLI job (`app/scheduler/weekly.py`) is available for manual testing. Operators can test via `/admin` before releases.

This layered approach keeps human oversight (admin console) while letting specialized agents perform scraping, reasoning, and communication.

Enjoy the ride — and feel free to plug in new leagues, channels, or schedulers as FFZ evolves. ⚽
