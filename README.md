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
- **Scheduler** – APScheduler inside the API plus CLI runner (`app/scheduler/jobs.py`, `app/scheduler/weekly.py`).
- **Admin UI** – one-page console (`app/api/admin_page.py`, `app/static/admin.js`).

Key agentic steps:
1. `scrape.run` routes fetch BBC standings/fixtures/scorers (respect robots + allowlist) and cache snapshots.
2. `report_builder` assembles per-user facts, calls the LLM, and falls back to deterministic copy if the model throttles (429, etc.).
3. Delivery agents format multi-channel content, chunk WhatsApp, or assemble long-form HTML/plain emails.
4. The scheduler orchestrates generation for all active users; operators fire `/news/send_latest` to push WhatsApp/email, or integrate mailing into cron later.

---

### Repo Map

| Path | Purpose |
| --- | --- |
| `app/api/*.py` | HTTP routers: auth, news, admin page, scraping, subscriptions. |
| `app/data/extractor/leagues.py` | BBC parsing logic (standings, fixtures, scorers). |
| `app/news/llm_generator.py` | LLM wrapper (Mistral/OpenAI). |
| `app/services/formatter.py` | Channel-specific formatting (WhatsApp chunks + email bodies). |
| `app/services/email_sender.py` / `whatsapp_sender.py` | Delivery integrations (Maileroo & CallMeBot). |
| `app/scheduler/jobs.py` | APScheduler registration (weekly Mondays 09:00 Europe/Paris). |
| `app/scheduler/weekly.py` | CLI scheduler runner for cron/manual triggers. |
| `app/models/*` | SQLAlchemy models (`User`, `Subscription`, `Snapshot`, `WeeklyReport`). |
| `migrations/` | Alembic migrations (run via `alembic upgrade head`). |
| `docker/docker-compose.yml` & `docker/Dockerfile` | Runtime packaging. |

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

# Apply migrations (first run or after schema changes)
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# Restart to clear schema guard / reload scheduler
docker compose -f docker/docker-compose.yml restart api

# Tail logs
docker compose -f docker/docker-compose.yml logs -f api
```

- Admin console: `http://localhost:8000/admin`
  - Register/login, follow leagues, run `Scrape preview`, `Run scrape job`, `Generate weekly report`.
  - Choose delivery channel (WhatsApp or Email) before pressing “Send latest report.”

---

### Scheduler & Cron

- APScheduler registers on API startup (`schedule_jobs`).  
  - Default cadence: every Monday 09:00 Europe/Paris.  
  - Override with `FFZ_SCHEDULER_INTERVAL_MINUTES=<int>` for faster loops.
- Manual run (inside container):

```bash
docker compose -f docker/docker-compose.yml exec api python -m app.scheduler.weekly
```

This walks every subscribed user, runs `generate_and_store_weekly_report`, and prints a summary (`success/failed`). Delivery (WhatsApp/email) still happens via `/news/send_latest` so operators can pick the channel per user; extend the scheduler if you want auto-send after generation.

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

- **Schema guard 503** – Run migrations (`alembic upgrade head`), then restart the API to clear `SCHEMA_ERROR_MSG`.
- **`sqlite3.OperationalError: table X already exists`** – Delete/rename `ffz.db`, rerun migrations.
- **Mistral 429 (tier capacity)** – The agent falls back to deterministic copy (`quality_guard`). Switch LLM provider or throttle usage to avoid repeated fallbacks.
- **WhatsApp skipped** – Ensure `.env` has `WA_PHONE` & `WA_API_KEY`, and that the phone is registered with CallMeBot.
- **Maileroo skipped** – Check `MAILEROO_API_KEY` and default sender fields. Logs show reference IDs for successful sends.
- **Admin send button disabled** – You must `Generate weekly report` first (per-user cache). Use `Show latest report` to confirm payload before sending.

---

### Why “Agentic”?

Each stage is autonomous yet coordinated:

1. **Data agent** – Scraper/normalizer fetches live standings + fixtures + scorers, respects robots/allowlist, and snapshots results.
2. **Reasoning agent** – `report_builder` composes facts into prompts, lets the LLM plan narratives, and cross-checks with `quality_guard`.
3. **Delivery agents** – WhatsApp chunker enforces message limits, Maileroo builds HTML/plain text, both record status per user.
4. **Orchestrator** – APScheduler + CLI job decide when to execute the whole chain. Operators can test via `/admin` before releases.

This layered approach keeps human oversight (admin console) while letting specialized agents perform scraping, reasoning, and communication.

Enjoy the ride — and feel free to plug in new leagues, channels, or schedulers as FFZ evolves. ⚽
