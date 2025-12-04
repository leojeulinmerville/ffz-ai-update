"""
Billing API

Endpoints for Stripe integration and subscription management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.auth.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.services import stripe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    plan: str = "monthly"  # 'monthly' or 'yearly'
    promo_code: str = None


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequest = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Checkout session for subscription.
    
    Args:
        plan: 'monthly' (€2.90/mo) or 'yearly' (€25/year Season Pass)
        promo_code: Optional promo code (e.g., 'FFZ_FAN_CLUB')
    
    Returns checkout URL for user to complete payment.
    """
    plan = request.plan if request else "monthly"
    promo_code = request.promo_code if request else None
    
    try:
        # Create Stripe customer if doesn't exist
        if not user.stripe_customer_id:
            customer_id = await stripe_service.create_customer(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user.id)}
            )
            user.stripe_customer_id = customer_id
            await db.commit()
        
        # Create checkout session
        session = await stripe_service.create_checkout_session(
            customer_id=user.stripe_customer_id,
            user_id=str(user.id),
            plan=plan,
            promo_code=promo_code
        )
        
        return {
            "status": "success",
            "checkout_url": session["url"],
            "session_id": session["session_id"],
            "plan": session["plan"]
        }
        
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
async def create_portal(
    user: User = Depends(get_current_user)
):
    """
    Create a Stripe Customer Portal session for subscription management.
    
    Returns portal URL for user to manage their subscription.
    """
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")
    
    try:
        portal_url = await stripe_service.create_portal_session(
            customer_id=user.stripe_customer_id
        )
        
        return {
            "status": "success",
            "portal_url": portal_url
        }
        
    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_billing_status(
    user: User = Depends(get_current_user)
):
    """
    Get current billing and subscription status.
    
    Returns trial status, subscription status, billing info, and enforcement status.
    """
    from datetime import datetime, timezone, timedelta
    from app.middleware.subscription_guard import is_billing_enforcement_enabled
    import os
    
    trial_days = int(os.getenv("TRIAL_DURATION_DAYS", "15"))
    
    # Calculate trial info
    trial_active = user.is_trial_active()
    trial_days_remaining = None
    
    if user.trial_started_at and trial_active:
        trial_end = user.trial_started_at + timedelta(days=trial_days)
        days_left = (trial_end - datetime.now(timezone.utc)).days
        trial_days_remaining = max(0, days_left)
    
    # Get subscription info
    subscription_info = None
    if user.stripe_subscription_id:
        subscription_info = await stripe_service.get_subscription(user.stripe_subscription_id)
    
    # Check enforcement status
    enforcement_enabled = is_billing_enforcement_enabled()
    
    # Access is granted if enforcement is disabled OR user has active subscription
    has_access = (not enforcement_enabled) or user.has_active_subscription()
    
    return {
        "trial": {
            "active": trial_active,
            "started_at": user.trial_started_at.isoformat() if user.trial_started_at else None,
            "days_remaining": trial_days_remaining
        },
        "subscription": {
            "status": user.subscription_status,
            "stripe_customer_id": user.stripe_customer_id,
            "stripe_subscription_id": user.stripe_subscription_id,
            "details": subscription_info
        },
        "has_access": has_access,
        "enforcement_enabled": enforcement_enabled,
        "pricing": stripe_service.PRICING_INFO
    }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Processes subscription lifecycle events from Stripe.
    """
    try:
        # Get raw body
        payload = await request.body()
        
        # Verify and construct event
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        logger.info(f"Received Stripe webhook: {event['type']}")
        
        # Handle different event types
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"], db)
        
        elif event["type"] == "customer.subscription.updated":
            await handle_subscription_updated(event["data"]["object"], db)
        
        elif event["type"] == "customer.subscription.deleted":
            await handle_subscription_deleted(event["data"]["object"], db)
        
        elif event["type"] == "invoice.payment_failed":
            await handle_payment_failed(event["data"]["object"], db)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def handle_checkout_completed(session, db: AsyncSession):
    """Handle successful checkout completion."""
    user_id = session.get("metadata", {}).get("user_id")
    
    if not user_id:
        logger.warning("No user_id in checkout session metadata")
        return
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        logger.error(f"User {user_id} not found for checkout")
        return
    
    # Update user with subscription
    subscription_id = session.get("subscription")
    user.stripe_subscription_id = subscription_id
    user.subscription_status = "active"
    
    await db.commit()
    logger.info(f"User {user_id} subscription activated: {subscription_id}")


async def handle_subscription_updated(subscription, db: AsyncSession):
    """Handle subscription status changes."""
    customer_id = subscription.get("customer")
    
    # Find user by customer ID
    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalars().first()
    
    if not user:
        logger.warning(f"User not found for customer {customer_id}")
        return
    
    # Update subscription status
    status = subscription.get("status")
    user.subscription_status = status
    user.stripe_subscription_id = subscription.get("id")
    
    await db.commit()
    logger.info(f"User {user.id} subscription updated: {status}")


async def handle_subscription_deleted(subscription, db: AsyncSession):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")
    
    # Find user
    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalars().first()
    
    if not user:
        return
    
    # Update status
    user.subscription_status = "cancelled"
    
    await db.commit()
    logger.info(f"User {user.id} subscription cancelled")


async def handle_payment_failed(invoice, db: AsyncSession):
    """Handle failed payment."""
    customer_id = invoice.get("customer")
    
    # Find user
    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalars().first()
    
    if not user:
        return
    
    # Update status
    user.subscription_status = "past_due"
    
    await db.commit()
    logger.warning(f"User {user.id} payment failed - status: past_due")
