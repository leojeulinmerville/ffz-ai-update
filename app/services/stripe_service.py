"""
Stripe Service

Handles all Stripe billing operations including:
- Customer creation
- Checkout sessions
- Subscription management
- Webhook processing
"""

import os
import stripe
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:8000/dashboard?session_id={CHECKOUT_SESSION_ID}")
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", "http://localhost:8000/dashboard")


async def create_customer(email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
    """
    Create a Stripe customer.
    
    Args:
        email: Customer email
        name: Customer name
        metadata: Additional metadata
        
    Returns:
        Stripe customer ID
    """
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )
        logger.info(f"Created Stripe customer: {customer.id} for {email}")
        return customer.id
    except stripe.error.StripeError as e:
        logger.error(f"Failed to create Stripe customer: {e}")
        raise RuntimeError(f"Stripe error: {str(e)}")


async def create_checkout_session(
    customer_id: str,
    user_id: str,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Stripe Checkout session for subscription.
    
    Args:
        customer_id: Stripe customer ID
        user_id: Internal user ID
        success_url: Redirect URL on success
        cancel_url: Redirect URL on cancel
        
    Returns:
        Dict with session ID and URL
    """
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url or STRIPE_SUCCESS_URL,
            cancel_url=cancel_url or STRIPE_CANCEL_URL,
            metadata={
                "user_id": user_id
            },
            subscription_data={
                "metadata": {
                    "user_id": user_id
                }
            }
        )
        
        logger.info(f"Created checkout session: {session.id} for user {user_id}")
        
        return {
            "session_id": session.id,
            "url": session.url
        }
    except stripe.error.StripeError as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise RuntimeError(f"Stripe error: {str(e)}")


async def create_portal_session(customer_id: str, return_url: Optional[str] = None) -> str:
    """
    Create a Stripe Customer Portal session for subscription management.
    
    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to after portal
        
    Returns:
        Portal session URL
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url or STRIPE_CANCEL_URL
        )
        
        logger.info(f"Created portal session for customer: {customer_id}")
        return session.url
    except stripe.error.StripeError as e:
        logger.error(f"Failed to create portal session: {e}")
        raise RuntimeError(f"Stripe error: {str(e)}")


async def cancel_subscription(subscription_id: str) -> bool:
    """
    Cancel a Stripe subscription.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Returns:
        True if successful
    """
    try:
        stripe.Subscription.delete(subscription_id)
        logger.info(f"Cancelled subscription: {subscription_id}")
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise RuntimeError(f"Stripe error: {str(e)}")


async def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
    """
    Get subscription details.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Returns:
        Subscription data or None
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "customer": subscription.customer
        }
    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve subscription: {e}")
        return None


def construct_webhook_event(payload: bytes, sig_header: str) -> Optional[stripe.Event]:
    """
    Construct and verify a Stripe webhook event.
    
    Args:
        payload: Raw request body
        sig_header: Stripe signature header
        
    Returns:
        Verified Stripe event or None
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not set, skipping verification")
        return None
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return None
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return None
