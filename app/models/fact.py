import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String

from app.models.db import Base


def gen_uuid_str() -> str:
    return str(uuid.uuid4())


class Fact(Base):
    __tablename__ = "facts"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    job_id = Column(String, ForeignKey("scrape_jobs.id"), index=True, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    league_code = Column(String, nullable=False, index=True)
    team = Column(String, nullable=True, index=True)
    type = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    source_url = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    credibility = Column(Float, default=0.75)
    observed_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
