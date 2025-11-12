import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from app.models.db import Base


def gen_uuid_str() -> str:
    return str(uuid.uuid4())


class RawPage(Base):
    __tablename__ = "raw_pages"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    url = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    cache_key = Column(String, nullable=False, index=True)
    content_hash = Column(String, nullable=False)
    html = Column(Text, nullable=False)
    fetched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
