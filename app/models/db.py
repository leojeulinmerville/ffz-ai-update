import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

ECHO_SQL = bool(int(os.getenv("SQL_ECHO", "0")))

engine = create_async_engine(DATABASE_URL, echo=ECHO_SQL, future=True)
AsyncSessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
Base = declarative_base()


async def init_db() -> None:
    # Alembic manages the schema; nothing to do here.
    pass


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
