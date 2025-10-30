import os
from typing import List, Dict, Any
from mistralai import Mistral

# --- ENV ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

# Client Mistral
client = Mistral(api_key=MISTRAL_API_KEY)

# --- SYSTEM PROMPT ---
BASE_PROMPT = """You write short weekly football summaries in the user's language.

Input you receive:
- League name
- League table (team, points, rank)
- Optional favorite team

Style rules:
- Tone: energetic, like you're talking to a football fan, not corporate.
- ~6 to 8 short lines maximum.
- First line MUST look like a headline with the league name and an emoji. Example: "🏆 Ligue 1 – Weekly update"
- Mention who's leading and how tight the table is.
- If there's a favorite team, include a short focus on them near the end.
- You may use emojis like 🔥⚽📊 but no Markdown (**bold**, # headers, etc.).
- NO meta explanation like "Here is your summary:".

Return ONLY the final article text. No JSON, no extra commentary.
"""

async def generate_article(
    language: str,
    league_name: str,
    table: List[Dict[str, Any]],
    fav_team: str | None,
) -> str:
    """
    Build one personalized article block for this league.
    Falls back to a deterministic text if no API key is set.
    """

    # fallback local (dev sans clé Mistral)
    if not MISTRAL_API_KEY:
        leader = table[0]["team"] if table else "???"
        pts = table[0]["pts"] if table else "?"
        extra = ""
        if fav_team:
            extra = (
                f"\nFocus {fav_team}: on garde un œil sur leur forme, "
                f"prochain match décisif."
            )
        return (
            f"🏆 {league_name} – Weekly update\n"
            f"{leader} est en tête ({pts} pts). Le haut du classement reste serré.\n"
            f"{extra}".strip()
        )

    # format classement top 5 pour le prompt
    standings_lines = []
    for row in table[:5]:
        standings_lines.append(
            f"{row.get('rank')}. {row.get('team')} - {row.get('pts')} pts"
        )
    standings_block = "\n".join(standings_lines)

    # prompt utilisateur envoyé au modèle
    user_prompt = f"""
User language: {language}

League: {league_name}

Top of the table (rank. team - pts):
{standings_block}

Favorite team to highlight:
{fav_team or "None"}
"""

    # appel API Mistral (SDK officiel mistralai>=1.2)
    completion = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": BASE_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=300,
    )

    return completion.choices[0].message.content.strip()
