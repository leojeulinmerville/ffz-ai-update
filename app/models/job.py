import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String

from app.models.db import Base


def gen_uuid_str() -> str:
    return str(uuid.uuid4())


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    user_id = Column(String, nullable=False, index=True)
    status = Column(String, default="queued", index=True)
    leagues = Column(JSON, default=list)
    teams = Column(JSON, default=list)
    time_window_days = Column(Integer, default=45)
    force_playwright = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(String, nullable=True)
    last_source = Column(String, nullable=True)
    totals = Column(JSON, default=dict)
