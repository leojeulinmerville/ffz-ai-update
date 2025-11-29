"""
Subscription Guard Middleware

Protects premium endpoints by checking if user has active subscription or trial.
"""

from fastapi import HTTPException, Depends
from app.auth.security import get_current_user
from app.models.user import User


async def require_active_subscription(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures user has an active subscription (trial or paid).
    
    Raises:
        HTTPException: 403 if user doesn't have active subscription
    
    Returns:
        User object if subscription is active
    """
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
