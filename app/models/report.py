import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.db import Base

def gen_uuid_str() -> str:
    return str(uuid.uuid4())

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    content = Column(JSON, nullable=False)  # The generated report structure
    language = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    team_focus = Column(String, nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Delivery tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String, default="pending")  # pending, sent, failed
    delivery_error = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="reports")
