import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.db import Base


def gen_uuid_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language = Column(String, default="fr")
    favorite_team = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Billing & Trial
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, default="trial")  # trial, active, cancelled, past_due
    trial_started_at = Column(DateTime(timezone=True), nullable=True)

    # Preferences
    tone = Column(String, default="neutral")  # fan, neutral, analytic, bettor
    frequency = Column(String, default="weekly")  # weekly, biweekly, monthly
    
    # Report tracking
    last_report_sent_at = Column(DateTime(timezone=True), nullable=True)

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]
    
    def is_trial_active(self) -> bool:
        """Check if user's trial is still active."""
        if not self.trial_started_at:
            return False
        
        from datetime import datetime, timezone, timedelta
        import os
        
        trial_days = int(os.getenv("TRIAL_DURATION_DAYS", "15"))
        trial_end = self.trial_started_at + timedelta(days=trial_days)
        
        return datetime.now(timezone.utc) < trial_end
    
    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription (trial or paid)."""
        return self.is_trial_active() or self.subscription_status == "active"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=gen_uuid_str)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    league = Column(String, nullable=False)
    team = Column(String, nullable=True)
    frequency = Column(String, default="weekly")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subscriptions")
