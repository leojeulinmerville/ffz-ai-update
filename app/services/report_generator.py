"""
Report Generator Service

Orchestrates the generation of personalized weekly football reports using GPT-4o.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, Subscription
from app.models.report import Report
from app.services.context_builder import build_team_context
from app.services.llm_prompts import build_report_prompt

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_openai = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def generate_weekly_report(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Generate a personalized weekly report for a user.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        Dict containing the generated report
    
    Raises:
        ValueError: If user not found or has no subscriptions
        RuntimeError: If OpenAI is not configured or generation fails
    """
    if not _openai:
        raise RuntimeError("OpenAI not configured. Set OPENAI_API_KEY environment variable.")
    
    # Fetch user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Get user preferences
    language = (user.language or "en").lower()
    tone = (user.tone or "neutral").lower()  # Use user's tone preference
    
    # Fetch active subscriptions
    subs_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True
        )
    )
    subscriptions = subs_result.scalars().all()
    
    if not subscriptions:
        raise ValueError(f"User {user_id} has no active subscriptions")
    
    # For MVP, generate report for the first subscription (primary team)
    # Later: support multiple teams/leagues
    primary_sub = subscriptions[0]
    team_name = primary_sub.team or user.favorite_team
    league_code = primary_sub.league
    
    if not team_name:
        raise ValueError(f"No team specified for user {user_id}")
    
    logger.info(f"Generating report for user {user_id}: {team_name} ({league_code}), lang={language}, tone={tone}")
    
    # Build context from database
    context = await build_team_context(team_name, league_code, db, weeks=4)
    
    # Build prompts
    prompts = build_report_prompt(context, language, tone)
    
    # Call GPT-4o
    try:
        response = await _openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompts["system"]},
                {"role": "user", "content": prompts["user"]}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        report_data = json.loads(content)
        
    except Exception as exc:
        logger.exception(f"OpenAI report generation failed: {exc}")
        raise RuntimeError(f"Report generation failed: {exc}")
    
    # Construct full report payload
    report_payload = {
        "headline": report_data.get("headline", f"Weekly Report for {team_name}"),
        "sections": report_data.get("sections", []),
        "team_name": team_name,
        "league_code": league_code,
        "language": language,
        "tone": tone,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "context_summary": {
            "recent_matches_count": len(context.get("recent_matches", [])),
            "form": context.get("form", ""),
            "upcoming_matches_count": len(context.get("upcoming_matches", []))
        }
    }
    
    # Store report in database
    report = Report(
        user_id=user_id,
        content=report_payload,
        language=language,
        tone=tone,
        team_focus=team_name,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    logger.info(f"Report generated and stored: {report.id}")
    
    return {
        "id": str(report.id),
        "report": report_payload
    }


async def get_latest_report(user_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Get the user's most recent report.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        Report dict or None if no reports exist
    """
    result = await db.execute(
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(Report.generated_at.desc())
        .limit(1)
    )
    report = result.scalars().first()
    
    if not report:
        return None
    
    return {
        "id": str(report.id),
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "team_focus": report.team_focus,
        "language": report.language,
        "tone": report.tone,
        "report": report.content
    }
