"""
Subscription Guard Middleware

Protects premium endpoints by checking if user has active subscription or trial.
Can be disabled via BILLING_ENFORCEMENT_ENABLED environment variable.
"""

import os
from fastapi import HTTPException, Depends
from app.auth.security import get_current_user
from app.models.user import User


def is_billing_enforcement_enabled() -> bool:
    """Check if billing enforcement is enabled via environment variable."""
    return os.getenv("BILLING_ENFORCEMENT_ENABLED", "false").lower() == "true"


async def require_active_subscription(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures user has an active subscription (trial or paid).
    
    When BILLING_ENFORCEMENT_ENABLED=false (default), all users are allowed.
    When BILLING_ENFORCEMENT_ENABLED=true, subscription/trial is required.
    
    Raises:
        HTTPException: 403 if billing is enforced and user doesn't have active subscription
    
    Returns:
        User object (always returns if billing not enforced)
    """
    # If billing enforcement is disabled, allow all users
    if not is_billing_enforcement_enabled():
        return user
    
    # Billing enforcement is ON - check subscription status
    if not user.has_active_subscription():
        # Check if trial expired
        if user.trial_started_at and not user.is_trial_active():
            raise HTTPException(
                status_code=403,
                detail="Your trial has expired. Please subscribe to continue using FFZ."
            )
        
        # No subscription at all
        raise HTTPException(
            status_code=403,
            detail="Active subscription required. Please subscribe to access this feature."
        )
    
    return user
