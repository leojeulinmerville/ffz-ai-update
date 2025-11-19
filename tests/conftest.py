import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.db import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import Depends

TEST_DB_URL = "sqlite+aiosqlite:///./test_ffz.db"

engine_test = create_async_engine(TEST_DB_URL, echo=False, future=True)
AsyncSessionTest = sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)

async def override_init_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def get_test_db():
    async with AsyncSessionTest() as s:
        yield s

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    asyncio.get_event_loop().run_until_complete(override_init_db())

# override dependency
from app.auth.routes import get_db as get_db_prod
app.dependency_overrides[get_db_prod] = get_test_db

from app.api.subscriptions import get_db as get_db_subs
app.dependency_overrides[get_db_subs] = get_test_db

from app.api.scrape import get_db as get_db_scrape
app.dependency_overrides[get_db_scrape] = get_test_db

from app.api.facts import get_db as get_db_facts
app.dependency_overrides[get_db_facts] = get_test_db

from app.auth.security import get_db as get_db_security
app.dependency_overrides[get_db_security] = get_test_db

from app.api.news import get_db as get_db_news
app.dependency_overrides[get_db_news] = get_test_db

@pytest.fixture
def client():
    return TestClient(app)
