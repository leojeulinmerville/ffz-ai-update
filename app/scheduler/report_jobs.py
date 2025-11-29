"""
Weekly Report Jobs

Scheduled jobs for automated report generation and delivery
"""

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import AsyncSessionLocal
from app.models.user import User, Subscription
from app.models.report import Report
from app.services.report_generator import generate_weekly_report
from app.services.email_sender import send_report_email

logger = logging.getLogger(__name__)

# Configuration
TRIAL_DURATION_DAYS = int(os.getenv("TRIAL_DURATION_DAYS", "15"))
BATCH_SIZE = int(os.getenv("REPORT_BATCH_SIZE", "50"))


async def job_generate_weekly_reports():
    """
    Main weekly job: Generate and send reports to all active users.
    
    Runs every Monday 09:00 (configurable)
    """
    logger.info("Starting weekly report generation job")
    
    async with AsyncSessionLocal() as db:
        # Get all active users with subscriptions
        eligible_users = await get_eligible_users(db)
        
        logger.info(f"Found {len(eligible_users)} eligible users for reports")
        
        # Process in batches
        success_count = 0
        failure_count = 0
        
        for i in range(0, len(eligible_users), BATCH_SIZE):
            batch = eligible_users[i:i + BATCH_SIZE]
            logger.info(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} users)")
            
            for user in batch:
                try:
                    result = await process_user_report(user.id, db)
                    if result["status"] == "success":
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    logger.error(f"Failed to process report for user {user.id}: {e}")
                    failure_count += 1
        
        logger.info(f"Weekly report job completed: {success_count} sent, {failure_count} failed")


async def get_eligible_users(db: AsyncSession) -> List[User]:
    """
    Get all users eligible for weekly reports.
    
    Eligible users:
    - Have active subscriptions
    - Are in trial (trial_ends_at > now) OR have active subscription
    - Haven't received a report in the last 6 days
    """
    now = datetime.now(timezone.utc)
    six_days_ago = now - timedelta(days=6)
    
    # Query users with active subscriptions
    stmt = select(User).join(Subscription).where(
        and_(
            Subscription.is_active == True,
            User.is_active == True,
            User.is_verified == True,
            # Either in trial or active subscription
            (
                (User.trial_ends_at.isnot(None) & (User.trial_ends_at > now)) |
                (User.subscription_status == "active")
            ),
            # Haven't received report recently
            (
                User.last_report_sent_at.is_(None) |
                (User.last_report_sent_at < six_days_ago)
            )
        )
    ).distinct()
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return users


async def process_user_report(user_id: str, db: AsyncSession) -> dict:
    """
    Generate and send report for a single user.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Dict with status and details
    """
    logger.info(f"Processing report for user {user_id}")
    
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            return {"status": "error", "detail": "User not found"}
        
        # Generate report
        logger.info(f"Generating report for {user.email}")
        report_result = await generate_weekly_report(user_id, db)
        
        report_id = report_result["id"]
        report_payload = report_result["report"]
        
        # Send email
        logger.info(f"Sending report email to {user.email}")
        email_result = await send_report_email(
            report_payload,
            user.email,
            user.first_name
        )
        
        # Update report delivery status
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalars().first()
        
        if report:
            if email_result["status"] == "sent":
                report.sent_at = datetime.now(timezone.utc)
                report.delivery_status = "sent"
                
                # Update user's last_report_sent_at
                user.last_report_sent_at = datetime.now(timezone.utc)
                
                await db.commit()
                logger.info(f"Report {report_id} sent successfully to {user.email}")
                
                return {
                    "status": "success",
                    "report_id": report_id,
                    "email_status": email_result["status"]
                }
            else:
                report.delivery_status = "failed"
                report.delivery_error = email_result.get("detail", "Unknown error")
                await db.commit()
                
                logger.error(f"Failed to send report {report_id} to {user.email}: {email_result.get('detail')}")
                
                return {
                    "status": "failed",
                    "report_id": report_id,
                    "error": email_result.get("detail")
                }
        
        return {"status": "error", "detail": "Report not found after generation"}
        
    except Exception as e:
        logger.exception(f"Error processing report for user {user_id}: {e}")
        return {"status": "error", "detail": str(e)}


async def should_generate_report(user: User) -> bool:
    """
    Check if user should receive a report.
    
    Args:
        user: User object
        
    Returns:
        True if eligible, False otherwise
    """
    now = datetime.now(timezone.utc)
    
    # Must be active and verified
    if not user.is_active or not user.is_verified:
        return False
    
    # Must be in trial or have active subscription
    in_trial = user.trial_ends_at and user.trial_ends_at > now
    has_active_sub = user.subscription_status == "active"
    
    if not (in_trial or has_active_sub):
        return False
    
    # Check if report was sent recently (within last 6 days)
    if user.last_report_sent_at:
        six_days_ago = now - timedelta(days=6)
        if user.last_report_sent_at > six_days_ago:
            return False
    
    return True
