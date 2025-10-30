"""
generator.py
------------
Turns structured league data into a human-readable article.

Two tones:
- league recap: neutral journalist tone
- fan zone: focused on the user's favorite team if provided
"""

from typing import List, Dict, Optional

def _league_block_fr(league_name: str, table: List[Dict]) -> str:
    if not table:
        return f"Aucune donnée disponible pour {league_name} pour le moment.\n"

    leader = table[0]
    lines = [f"🏆 {league_name} – Point de la semaine"]
    lines.append(
        f"{leader['team']} reste en tête avec {leader['points']} points "
        f"après {leader['played']} matchs."
    )

    top4 = ", ".join([f"{row['position']}. {row['team']}" for row in table[:4]])
    lines.append(f"Top 4 actuel : {top4}.")

    lines.append("La dynamique du haut de tableau reste serrée et chaque point compte.\n")
    return "\n".join(lines)


def _league_block_en(league_name: str, table: List[Dict]) -> str:
    if not table:
        return f"No data available yet for {league_name}.\n"

    leader = table[0]
    lines = [f"🏆 {league_name} – Weekly Overview"]
    lines.append(
        f"{leader['team']} stays on top with {leader['points']} points "
        f"after {leader['played']} matches."
    )

    top4 = ", ".join([f"{row['position']}. {row['team']}" for row in table[:4]])
    lines.append(f"Current Top 4: {top4}.")

    lines.append("The title race is still tight, and every point matters.\n")
    return "\n".join(lines)


def _fan_block_fr(fav_team: str, table: List[Dict]) -> str:
    # find team
    found = None
    for row in table:
        if row["team"].lower() == fav_team.lower():
            found = row
            break

    if not found:
        return (
            f"💙 Focus {fav_team}\n"
            f"Ton club {fav_team} n'apparaît pas dans le top actuel. "
            "On continue à surveiller pour la semaine prochaine.\n"
        )

    return (
        f"💙 Focus {fav_team}\n"
        f"{fav_team} est actuellement {found['position']}ᵉ avec {found['points']} points "
        f"en {found['played']} matchs joués.\n"
        "On surveille la forme, les prochains matchs et les points clés.\n"
    )


def _fan_block_en(fav_team: str, table: List[Dict]) -> str:
    found = None
    for row in table:
        if row["team"].lower() == fav_team.lower():
            found = row
            break

    if not found:
        return (
            f"💙 {fav_team} focus\n"
            f"{fav_team} is currently outside the top positions. "
            "We'll keep tracking next week.\n"
        )

    return (
        f"💙 {fav_team} focus\n"
        f"{fav_team} sits {found['position']} with {found['points']} points "
        f"after {found['played']} matches.\n"
        "We'll keep an eye on form, injuries and upcoming fixtures.\n"
    )


def generate_article(
    language: str,
    league_name: str,
    table: List[Dict],
    fav_team: Optional[str] = None,
) -> str:
    """
    Returns final text block (string).
    language: "fr" or "en"
    """

    if language.lower().startswith("fr"):
        league_txt = _league_block_fr(league_name, table)
        if fav_team:
            fan_txt = _fan_block_fr(fav_team, table)
        else:
            fan_txt = ""
    else:
        league_txt = _league_block_en(league_name, table)
        if fav_team:
            fan_txt = _fan_block_en(fav_team, table)
        else:
            fan_txt = ""

    return league_txt + "\n" + fan_txt
