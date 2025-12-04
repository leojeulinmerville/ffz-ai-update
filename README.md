# Football Fan Zone (FFZ) - AI-Powered Football Insights

**Your personal football journalist: data-driven, multi-lingual, delivered every week.**

FFZ is a comprehensive B2C SaaS platform that transforms raw football match data into personalized, narrative-driven reports for fans worldwide. By leveraging advanced scraping, computer vision, and Generative AI, FFZ delivers tailored insights based on your favorite teams, preferred language, and desired tone.

---

## ⚡ What It Does

1.  **Data Collection**: Automatically scrapes match schedules, results, and detailed statistics from major sports platforms using a robust multi-agent pipeline.
2.  **AI Analysis**: Uses GPT-4o to analyze match facts, player performance, and statistical trends, converting numbers into engaging narratives.
3.  **Personalization**: Generates reports in multiple languages (English, French, Spanish) and tones (Fan, Neutral, Analytic, Bettor) to match user preferences.
4.  **Delivery**: Delivers insights via a modern web dashboard and automated email notifications.
5.  **Monetization**: Integrated Stripe billing system for premium subscriptions with trial periods.

---

## 🛠️ Tech Stack

*   **Backend**: FastAPI (Python 3.12), AsyncIO
*   **Frontend**: Vue.js 3, Tailwind CSS
*   **Database**: PostgreSQL 15, SQLAlchemy, Alembic
*   **AI & ML**: OpenAI GPT-4o, Playwright (Computer Vision)
*   **Infrastructure**: Docker, Docker Compose
*   **Billing**: Stripe Integration
*   **Scheduling**: APScheduler

---

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Prerequisites

*   **Docker Desktop** (Recommended)
*   *Or* Python 3.12+ and PostgreSQL 15+ for manual setup

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd ffz-ai-update
    ```

2.  **Configure Environment**
    Create a `.env` file in the root directory by copying the example.
    ```bash
    cp .env.example .env
    ```
    *Open `.env` and fill in your API keys (OpenAI, Stripe, Database credentials, etc.).*

3.  **Start with Docker**
    Build and run the containerized application.
    ```bash
    docker-compose -f docker/docker-compose.yml up --build -d
    ```

4.  **Apply Database Migrations**
    Initialize the database schema.
    ```bash
    docker-compose -f docker/docker-compose.yml exec api alembic upgrade head
    ```

### Access Points

*   **Web Interface**: [http://localhost:8000](http://localhost:8000)
*   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Admin Dashboard**: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🎮 Usage Guide

### 1. User Onboarding
*   Navigate to the web interface.
*   Register a new account.
*   Complete the onboarding wizard: select your language, favorite team, and report tone.
*   **Trial**: A 15-day premium trial starts automatically upon registration.

### 2. Dashboard & Reports
*   **Dashboard**: View your active trial status, subscription details, and latest reports.
*   **Generate Report**: Click "Generate New Report" to trigger an on-demand analysis of your team's latest performance.
*   **Billing**: Manage your subscription via the integrated Stripe portal.

### 3. Administration
*   Access the admin panel to monitor users and system status.
*   Manually trigger scraping jobs or report generation cycles via the API or command line.

---

## 📂 Project Structure

```
ffz-ai-update/
├── app/
│   ├── api/            # REST API endpoints (Auth, Reports, Billing)
│   ├── models/         # Database models (User, Match, Subscription)
│   ├── services/       # Core logic (AI, Scraping, Stripe, Email)
│   ├── scheduler/      # Background jobs configuration
│   ├── static/         # Vue.js Frontend assets
│   └── main.py         # Application entry point
├── docker/             # Docker configuration files
├── migrations/         # Database migration scripts
├── .env.example        # Environment variable template
└── requirements.txt    # Python dependencies
```

---

## 🐳 Useful Commands

**View Logs**
```bash
docker-compose -f docker/docker-compose.yml logs -f api
```

**Restart API Service**
```bash
docker-compose -f docker/docker-compose.yml restart api
```

**Stop Services**
```bash
docker-compose -f docker/docker-compose.yml down
```

**Run Tests**
```bash
docker-compose -f docker/docker-compose.yml exec api python -m pytest
```
