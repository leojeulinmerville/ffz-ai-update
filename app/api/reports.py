"""
Reports API

Endpoints for generating and retrieving personalized football reports.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.middleware.subscription_guard import require_active_subscription
from app.database import get_db
from app.models.user import User
from app.services.report_generator import generate_weekly_report, get_latest_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
async def generate_report(
    send_email: bool = True,  # New parameter
    user: User = Depends(require_active_subscription),  # Protected!
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new weekly report for the current user.
    
    This endpoint:
    1. Fetches user's subscriptions and preferences
    2. Builds context from recent matches in the database
    3. Calls GPT-4o to generate a personalized report
    4. Stores the report in the database
    5. Optionally sends the report via email
    6. Returns the generated report
    """
    try:
        result = await generate_weekly_report(str(user.id), db)
        
        # Send email if requested
        if send_email:
            from app.services.email_sender import send_report_email
            from datetime import datetime, timezone
            from sqlalchemy import select
            from app.models.report import Report
            
            # Get the report we just created
            report_id = result["id"]
            stmt = select(Report).where(Report.id == report_id)
            db_result = await db.execute(stmt)
            report = db_result.scalars().first()
            
            if report:
                # Send email
                email_result = await send_report_email(
                    result["report"],
                    user.email,
                    user.first_name
                )
                
                # Update delivery status
                if email_result["status"] == "sent":
                    report.sent_at = datetime.now(timezone.utc)
                    report.delivery_status = "sent"
                    await db.commit()
        
        return {
            "status": "success",
            "message": "Report generated successfully" + (" and sent by email" if send_email else ""),
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/latest")
async def get_latest_report_endpoint(
    user: User = Depends(require_active_subscription),  # Protected!
    db: AsyncSession = Depends(get_db)
):
    """
    Get the user's most recent report.
    
    Returns 404 if no reports exist for this user.
    """
    report = await get_latest_report(str(user.id), db)
    
    if not report:
        raise HTTPException(status_code=404, detail="No reports found for this user")
    
    return {
        "status": "success",
        "data": report
    }
