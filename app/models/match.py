import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Integer, JSON, ForeignKey, Enum as SqlEnum
import enum
from sqlalchemy.orm import relationship
from app.models.db import Base

def gen_uuid_str() -> str:
    return str(uuid.uuid4())

class MatchStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    source_id = Column(String, index=True, nullable=True, unique=True) # External ID (e.g. ESPN ID)
    league_code = Column(String, index=True, nullable=False)
    home_team = Column(String, index=True, nullable=False)
    away_team = Column(String, index=True, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default=MatchStatus.SCHEDULED.value)
    score_home = Column(Integer, nullable=True)
    score_away = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    facts = relationship("MatchFacts", back_populates="match", cascade="all, delete-orphan")

class MatchFacts(Base):
    __tablename__ = "match_facts"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, index=True)
    source = Column(String, nullable=False)  # e.g., "bbc", "flashscore_vision"
    stats = Column(JSON, nullable=True)  # Structured stats (possession, shots, etc.)
    key_events = Column(JSON, nullable=True)  # Goals, cards, subs
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    match = relationship("Match", back_populates="facts")
