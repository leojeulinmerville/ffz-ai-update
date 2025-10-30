from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db.database import Base

def gen_uuid_str():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid_str)     # <-- String
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    language = Column(String, default="en")
    favorite_team = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    subscriptions = relationship("Subscription", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True, default=gen_uuid_str)      # <-- String
    user_id = Column(String, ForeignKey("users.id"))                 # <-- String FK
    league = Column(String, nullable=False)
    team = Column(String, nullable=True)
    frequency = Column(String, default="weekly")
    is_active = Column(Boolean, default=True)
    user = relationship("User", back_populates="subscriptions")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    language = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    delivery_status = Column(String, default="generated")
    created_at = Column(DateTime, default=datetime.utcnow)
