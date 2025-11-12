import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from app.models.db import Base


def gen_uuid_str() -> str:
    return str(uuid.uuid4())


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    league_code = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    facts_count = Column(Integer, default=0)
    sources_used = Column(JSON, default=list)
    payload = Column(JSON, nullable=False)
