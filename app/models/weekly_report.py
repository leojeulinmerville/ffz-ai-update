import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.models.db import Base


def gen_uuid_str() -> str:
    return str(uuid.uuid4())


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    language = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    delivery_status = Column(String, default="generated")
    delivery_channel = Column(String, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
