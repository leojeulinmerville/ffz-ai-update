# Football Fan Zone – AI Weekly Companion

**Your personal football journalist: data-driven, multi-lingual, delivered every week.**

FFZ is a B2C SaaS that generates personalized weekly football reports for fans worldwide. It scrapes match data, analyzes stats with AI, and delivers tailored reports in your language and tone preference.

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (recommended) OR
- **Python 3.12+** + **PostgreSQL 15+** (for local development)

### Option 1: Docker (Recommended)

```bash
# 1. Clone and navigate
cd ffz-ai-update

# 2. Create .env file (see Environment Variables below)
cp .env.example .env
# Edit .env with your keys

# 3. Start services
docker-compose -f docker/docker-compose.yml up --build -d

# 4. Apply migrations
docker-compose -f docker/docker-compose.yml exec api alembic upgrade head

# 5. Access the app
# Frontend: http://localhost:8000
# Admin: http://localhost:8000/admin
# Health: http://localhost:8000/health
```

### Option 2: Local Development

```bash
# 1. Install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Setup PostgreSQL
# Create database 'ffz_db' with user 'postgres:postgres'
python create_db.py

# 3. Apply migrations
python -m alembic upgrade head

# 4. Run the app
python -m uvicorn app.main:app --reload

# Access: http://127.0.0.1:8000
```

---

## 📋 Stack at a Glance

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (async) |
| **Database** | PostgreSQL 15 + Alembic migrations |
| **Frontend** | Vue 3 SPA + Tailwind CSS |
| **AI** | OpenAI GPT-4o (text + vision) |
| **Scraping** | httpx + BeautifulSoup + Playwright |
| **Email** | Maileroo |
| **Scheduler** | APScheduler (cron/interval jobs) |
| **Deployment** | Docker + docker-compose |

---

## 🏗️ Architecture

### Agentic Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Scraper   │────▶│   Context    │────▶│     LLM     │────▶│ Delivery │
│   Agent     │     │   Builder    │     │   Agent     │     │  Agent   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
      │                    │                     │                  │
   ESPN/BBC          Match Facts          GPT-4o Report        Email/SMS
  Flashscore         + Stats              Multi-lang          (Future)
                                          Multi-tone
```

**Flow:**
1. **Scraper Agent**: Fetches match data from ESPN/Flashscore, uses Playwright Vision for advanced stats
2. **Context Builder**: Structures data (recent matches, form, league position)
3. **LLM Agent**: GPT-4o generates personalized report in user's language/tone
4. **Delivery Agent**: Sends via email (Maileroo), stores in DB for dashboard

### Data Mutualization

- **Scrape once per match**, not per user
- Store normalized `Match` and `MatchFacts` in DB
- Generate reports by reading from DB (no re-scraping)
- **Cost optimization**: ~few cents per user/month

---

## 🎯 Key Features

### ✅ Implemented (Phases 1-4)

- **Landing Page**: Hero, features, pricing, FAQ
- **Auth & Onboarding**: Email verification, multi-step wizard (language, team, tone)
- **Data Pipeline**: 
  - Mutualized scraping (ESPN for matches, Flashscore Vision for stats)
  - Scheduled jobs (daily league scrape, hourly match facts)
- **Report Generation**:
  - Multi-language (FR/EN/ES)
  - 4 tones (fan/neutral/analytic/bettor)
  - Structured sections (This Week, Stats, Key Players, What's Next)
  - Interpretation over raw stats

### 🚧 In Progress (Phase 5)

- Weekly scheduling & email delivery
- Report archives
- Billing & trial logic (Stripe)

---

## 📁 Project Structure

```
ffz-ai-update/
├── app/
│   ├── api/              # API endpoints
│   │   ├── reports.py    # Report generation & retrieval
│   │   ├── onboarding.py # User onboarding flow
│   │   └── ...
│   ├── models/           # SQLAlchemy models
│   │   ├── match.py      # Match & MatchFacts
│   │   ├── report.py     # Generated reports
│   │   └── user.py       # User & Subscription
│   ├── services/         # Business logic
│   │   ├── report_generator.py    # Main report orchestration
│   │   ├── llm_prompts.py         # Multi-language prompts
│   │   ├── context_builder.py     # Data fetching
│   │   ├── scraper_service.py     # Scraping orchestration
│   │   └── email_sender.py        # Maileroo integration
│   ├── data/             # Data fetching & extraction
│   │   ├── scraper.py    # ESPN scraping
│   │   └── extractor/
│   │       └── vision.py # Playwright Vision for Flashscore
│   ├── scheduler/        # Scheduled jobs
│   │   ├── jobs.py       # Job registration
│   │   └── scraping_jobs.py  # Scraping jobs
│   ├── static/           # Frontend (Vue SPA)
│   │   ├── js/
│   │   │   ├── app.js    # Main Vue app
│   │   │   └── components/
│   │   │       ├── Landing.js
│   │   │       ├── Dashboard.js
│   │   │       └── Onboarding.js
│   │   └── index.html
│   └── main.py           # FastAPI app entry
├── migrations/           # Alembic migrations
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env                  # Environment variables
├── requirements.txt
└── README.md
```

---

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```ini
# Database (Docker uses postgres service, local uses localhost)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ffz_db

# Public URL (for email verification links)
PUBLIC_URL=http://127.0.0.1:8000

# OpenAI (REQUIRED for report generation)
OPENAI_API_KEY=sk-...

# Maileroo (for email delivery)
MAILEROO_API_KEY=...
MAILEROO_DEFAULT_FROM=no-reply@yourdomain.maileroo.org
MAILEROO_FROM_NAME=Football Fan Zone

# Security
SECRET_KEY=your-secret-key-here

# Optional
TZ=Europe/Paris
ECHO_SQL=false
```

---

## 🎮 Usage

### 1. Register & Onboard

1. Go to `http://localhost:8000`
2. Click "Get Started" → Register
3. Complete onboarding:
   - Choose language (FR/EN/ES)
   - Select favorite team & leagues
   - Pick report tone (fan/neutral/analytic/bettor)

### 2. Generate Report

**Via API:**
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"yourpassword"}'

# Generate report
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Authorization: Bearer <token>"

# Get latest report
curl http://localhost:8000/api/reports/latest \
  -H "Authorization: Bearer <token>"
```

**Via Dashboard:**
- Navigate to Reports tab
- Click "Generate New Report"

### 3. Admin Console

Access: `http://localhost:8000/admin`

Features:
- View all users
- Trigger scraping jobs
- Monitor system health

---

## 🔄 Scheduler & Jobs

### Automatic Jobs

- **Daily League Scrape** (02:00 AM): Fetches match schedules for all leagues
- **Hourly Match Facts** (every hour): Scrapes stats for recently finished matches
- **Weekly Reports** (Coming in Phase 5): Generates and sends reports

### Manual Triggers

```bash
# Docker
docker-compose -f docker/docker-compose.yml exec api python -m app.scheduler.weekly

# Local
python -m app.scheduler.weekly
```

---

## 🧪 Testing

### Run Tests

```bash
# Docker
docker-compose -f docker/docker-compose.yml exec api python -m pytest -v

# Local
python -m pytest -v
```

### Manual Testing

1. **Scraper Test**:
   ```bash
   python test_scraper.py
   ```

2. **Report Generation**:
   - Requires: User with subscriptions + match data in DB
   - Call `POST /api/reports/generate`

---

## 🐳 Docker Commands

```bash
# Start services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f api

# Restart
docker-compose -f docker/docker-compose.yml restart api

# Stop
docker-compose -f docker/docker-compose.yml down

# Rebuild
docker-compose -f docker/docker-compose.yml up --build -d

# Run migrations
docker-compose -f docker/docker-compose.yml exec api alembic upgrade head

# Access shell
docker-compose -f docker/docker-compose.yml exec api bash
```

---

## 🔍 Troubleshooting

### Docker Won't Start

**Issue**: `unable to get image 'docker-api'`

**Solution**: Make sure Docker Desktop is running. If still failing, try:
```bash
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up --build -d
```

### Profile Update Error

**Issue**: `InvalidRequestError: Instance '<User>' is not persistent`

**Solution**: Fixed in latest version. Make sure you've pulled latest code.

### Verification Email Shows localhost

**Issue**: Email contains `http://localhost:8000/verify?token=...`

**Solution**: Set `PUBLIC_URL` in `.env`:
```ini
PUBLIC_URL=https://yourdomain.com  # Production
PUBLIC_URL=http://127.0.0.1:8000   # Local testing
```

### No Reports Generated

**Checklist**:
1. User has active subscriptions? (`/api/user/profile`)
2. Match data exists in DB? (Run scraper: `python test_scraper.py`)
3. `OPENAI_API_KEY` is set in `.env`?
4. Check logs for errors

### Database Migration Issues

```bash
# Check current revision
docker-compose -f docker/docker-compose.yml exec api alembic current

# Generate new migration
docker-compose -f docker/docker-compose.yml exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose -f docker/docker-compose.yml exec api alembic upgrade head
```

---

## 📊 Roadmap

### ✅ Phase 0-4 (Complete)
- PostgreSQL migration
- Landing & onboarding
- Data pipeline (scrapers + vision)
- Report generation (multi-language, multi-tone)

### 🚧 Phase 5 (In Progress)
- Weekly scheduling
- Email delivery automation
- Report archives

### 📅 Phase 6 (Planned)
- Stripe billing integration
- 15-day trial logic
- Subscription management

---

## 🤝 Contributing

This is a private SaaS project. For questions or issues, contact the development team.

---

## 📝 License

Proprietary - All rights reserved

---

## 🆘 Support

- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
- **Logs**: `docker-compose -f docker/docker-compose.yml logs -f api`

---

**Built with ❤️ for football fans worldwide**
