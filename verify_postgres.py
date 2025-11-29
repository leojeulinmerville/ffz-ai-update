import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Use the URL from config (hardcoded here for standalone test if needed, but better to import)
# We'll try to import from app.config first, fallback to hardcoded if path issues
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.config import DATABASE_URL
except ImportError:
    DATABASE_URL = "postgresql+asyncpg://ffz_user:ffz_password@localhost:5432/ffz_db"

async def verify():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Result: {result.scalar()}")
        print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify())
