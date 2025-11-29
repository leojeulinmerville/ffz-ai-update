import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
TZ = os.getenv("TZ", "Europe/Paris")

# Database (Postgres)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ffz_user:ffz_password@localhost:5432/ffz_db")

SCRAPE_TIME_WINDOW_DAYS = int(os.getenv("SCRAPE_TIME_WINDOW_DAYS", "45"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "7200"))
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "true").lower() == "true"
PROXY_URL = os.getenv("PROXY_URL")

DEFAULT_ALLOWED_DOMAINS = [
    "uefa.com",
    "ligue1.com",
    "premierleague.com",
    "bundesliga.com",
    "laliga.com",
    "legaseriea.it",
    "bbc.com",
    "lequipe.fr",
    "theathletic.com",
    "fbref.com",
    "understat.com",
    "transfermarkt.com",
]

ALLOWED_DOMAINS: List[str] = [
    domain.strip()
    for domain in os.getenv("ALLOWED_DOMAINS", ",".join(DEFAULT_ALLOWED_DOMAINS)).split(",")
    if domain.strip()
]
