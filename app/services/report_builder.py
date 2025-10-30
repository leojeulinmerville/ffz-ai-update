"""
report_builder.py
-----------------
Core service that assembles the personalized weekly report for ONE user.
Now uses Mistral LLM for real article generation.
"""

from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import models
from app.news.fetch_standings import get_league_table
from app.news.llm_generator import generate_article


async def build_user_weekly_report(user_id: str, db: AsyncSession) -> Dict:
    """
    Builds a personalized report for one user.

    Returns:
    {
        "user": {
            "email": "...",
            "language": "fr",
        },
        "articles": [
            {
                "league_code": "FRA1",
                "league_name": "Ligue 1",
                "text": "...",
            },
            ...
        ]
    }
    """
    # ---------- Fetch user ----------
    result_user = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result_user.scalars().first()
    if not user:
        raise ValueError("User not found")

    # ---------- Fetch subscriptions ----------
    result_subs = await db.execute(
        select(models.Subscription).where(
            models.Subscription.user_id == user_id,
            models.Subscription.is_active == True,
        )
    )
    subs = result_subs.scalars().all()
    if not subs:
        return {
            "user": {"email": user.email, "language": user.language},
            "articles": [],
        }

    # ---------- Build articles ----------
    articles: List[Dict] = []
    for sub in subs:
        league_code = sub.league
        fav_team = sub.team or "une équipe de la ligue"

        # Get league data (scraper or API)
        league_data = await get_league_table(league_code)
        league_name = league_data.get("league_name", league_code)
        table = league_data.get("table", "")

        try:
            # Generate text with Mistral LLM
            text_block = generate_article(
                league_name=league_name,
                standings=table,
                team_focus=fav_team,
                language=user.language or "fr",
            )
        except Exception as e:
            text_block = f"(Erreur LLM pour {league_name}) {str(e)}"

        articles.append({
            "league_code": league_code,
            "league_name": league_name,
            "text": text_block.strip(),
        })

    return {
        "user": {
            "email": user.email,
            "language": user.language,
        },
        "articles": articles,
    }
