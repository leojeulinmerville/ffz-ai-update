import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
TZ = os.getenv("TZ", "Europe/Paris")

# SQLite par défaut (fichier)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ffz.db")
