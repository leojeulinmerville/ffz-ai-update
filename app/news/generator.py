from datetime import datetime

def generate_article(language: str, league: str, data: list, team: str | None = None):
    """Retourne un résumé textuel selon la langue et la team préférée."""
    date = datetime.now().strftime("%d %B %Y")
    top3 = ", ".join([d["team"] for d in data[:3]])

    if language == "fr":
        intro = f"🏆 Résumé du championnat {league} ({date})\n"
        content = f"Les trois premiers du classement sont : {top3}."
        if team:
            content += f" Ton équipe favorite, {team}, garde le cap !" if team in top3 else f" {team} devra redoubler d'efforts."
    else:
        intro = f"🏆 {league} League Recap ({date})\n"
        content = f"Top three teams are: {top3}."
        if team:
            content += f" Your team {team} is shining!" if team in top3 else f" {team} still has some work to do."

    return intro + "\n\n" + content
