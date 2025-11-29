"""
LLM Prompts for Football Report Generation

Supports:
- Languages: FR, EN, ES
- Tones: fan, neutral, analytic, bettor
"""

from typing import Dict, Any

# Language-specific section titles
SECTION_TITLES = {
    "fr": {
        "this_week": "Cette semaine pour {team}",
        "stats": "Ce que les stats révèlent",
        "key_players": "Joueurs clés & moments forts",
        "whats_next": "À venir"
    },
    "en": {
        "this_week": "This Week for {team}",
        "stats": "What the Stats Say",
        "key_players": "Key Players & Moments",
        "whats_next": "What's Next"
    },
    "es": {
        "this_week": "Esta semana para {team}",
        "stats": "Lo que dicen las estadísticas",
        "key_players": "Jugadores clave y momentos",
        "whats_next": "Qué sigue"
    }
}

# Tone definitions
TONE_INSTRUCTIONS = {
    "fan": {
        "fr": "Adopte un ton passionné et émotionnel. Utilise 'nous' et 'notre équipe'. Célèbre les victoires avec enthousiasme, sois dramatique sur les défaites. Montre de l'attachement émotionnel.",
        "en": "Adopt a passionate and emotional tone. Use 'we' and 'our team'. Celebrate wins with enthusiasm, be dramatic about losses. Show emotional attachment.",
        "es": "Adopta un tono apasionado y emocional. Usa 'nosotros' y 'nuestro equipo'. Celebra las victorias con entusiasmo, sé dramático con las derrotas. Muestra apego emocional."
    },
    "neutral": {
        "fr": "Adopte un ton objectif et équilibré, style journalistique. Utilise 'l'équipe' ou le nom du club. Présente les faits sans émotion excessive. Reste impartial.",
        "en": "Adopt an objective and balanced tone, journalistic style. Use 'the team' or club name. Present facts without excessive emotion. Stay impartial.",
        "es": "Adopta un tono objetivo y equilibrado, estilo periodístico. Usa 'el equipo' o nombre del club. Presenta los hechos sin emoción excesiva. Mantente imparcial."
    },
    "analytic": {
        "fr": "Adopte un ton analytique et technique. Concentre-toi sur les données (xG, possession, passes). Utilise du vocabulaire tactique. Explique les tendances statistiques.",
        "en": "Adopt an analytical and technical tone. Focus on data (xG, possession, passes). Use tactical vocabulary. Explain statistical trends.",
        "es": "Adopta un tono analítico y técnico. Concéntrate en los datos (xG, posesión, pases). Usa vocabulario táctico. Explica las tendencias estadísticas."
    },
    "bettor": {
        "fr": "Adopte un ton axé sur la forme et les paris. Mentionne les implications pour les cotes, l'impact des blessures, la valeur des matchs. Analyse la forme récente pour prédire les résultats.",
        "en": "Adopt a form and betting-focused tone. Mention odds implications, injury impact, match value. Analyze recent form to predict outcomes.",
        "es": "Adopta un tono centrado en la forma y las apuestas. Menciona las implicaciones de las cuotas, el impacto de las lesiones, el valor de los partidos. Analiza la forma reciente para predecir resultados."
    }
}

def build_report_prompt(context: Dict[str, Any], language: str, tone: str) -> Dict[str, str]:
    """
    Build the system and user prompts for report generation.
    
    Args:
        context: Dict containing team_name, recent_matches, league_position, stats, etc.
        language: 'fr', 'en', or 'es'
        tone: 'fan', 'neutral', 'analytic', or 'bettor'
    
    Returns:
        Dict with 'system' and 'user' prompts
    """
    lang = language.lower()
    tone_key = tone.lower()
    
    # Get section titles for this language
    titles = SECTION_TITLES.get(lang, SECTION_TITLES["en"])
    team_name = context.get("team_name", "the team")
    
    # System prompt
    system_prompts = {
        "fr": f"""Tu es un journaliste sportif expert spécialisé dans le football. 
Tu génères des rapports hebdomadaires personnalisés pour les fans.

{TONE_INSTRUCTIONS[tone_key][lang]}

IMPORTANT:
- Interprète les stats, ne te contente pas de les répéter (ex: "Cette domination de possession s'est traduite par un contrôle du jeu" au lieu de "60% de possession")
- Concentre-toi sur ce qui compte vraiment pour comprendre la performance
- Sois concis mais informatif (rapport de ~10 minutes de lecture)
- Structure ton rapport en sections claires
- Utilise un français naturel et fluide""",
        
        "en": f"""You are an expert sports journalist specializing in football.
You generate personalized weekly reports for fans.

{TONE_INSTRUCTIONS[tone_key][lang]}

IMPORTANT:
- Interpret stats, don't just repeat them (e.g., "This possession dominance translated to game control" instead of "60% possession")
- Focus on what really matters for understanding performance
- Be concise but informative (~10 minute read)
- Structure your report in clear sections
- Use natural, flowing English""",
        
        "es": f"""Eres un periodista deportivo experto especializado en fútbol.
Generas informes semanales personalizados para los aficionados.

{TONE_INSTRUCTIONS[tone_key][lang]}

IMPORTANTE:
- Interpreta las estadísticas, no solo las repitas (ej: "Este dominio de posesión se tradujo en control del juego" en lugar de "60% de posesión")
- Concéntrate en lo que realmente importa para entender el rendimiento
- Sé conciso pero informativo (lectura de ~10 minutos)
- Estructura tu informe en secciones claras
- Usa español natural y fluido"""
    }
    
    # User prompt with context
    user_prompts = {
        "fr": f"""Génère un rapport hebdomadaire pour {team_name}.

CONTEXTE:
{_format_context(context, lang)}

STRUCTURE REQUISE (JSON):
{{
    "headline": "Titre accrocheur du rapport (1 phrase)",
    "sections": [
        {{
            "title": "{titles['this_week'].format(team=team_name)}",
            "content": "Résumé de la semaine: résultats, dynamique, histoire"
        }},
        {{
            "title": "{titles['stats']}",
            "content": "Analyse des stats avec interprétation (xG, tirs, possession, tendances)"
        }},
        {{
            "title": "{titles['key_players']}",
            "content": "Joueurs en forme, moments décisifs"
        }},
        {{
            "title": "{titles['whats_next']}",
            "content": "Prochains matchs, enjeux, blessures potentielles"
        }}
    ]
}}""",
        
        "en": f"""Generate a weekly report for {team_name}.

CONTEXT:
{_format_context(context, lang)}

REQUIRED STRUCTURE (JSON):
{{
    "headline": "Catchy report headline (1 sentence)",
    "sections": [
        {{
            "title": "{titles['this_week'].format(team=team_name)}",
            "content": "Week summary: results, momentum, story"
        }},
        {{
            "title": "{titles['stats']}",
            "content": "Stats analysis with interpretation (xG, shots, possession, trends)"
        }},
        {{
            "title": "{titles['key_players']}",
            "content": "Players in form, decisive moments"
        }},
        {{
            "title": "{titles['whats_next']}",
            "content": "Upcoming fixtures, stakes, potential injuries"
        }}
    ]
}}""",
        
        "es": f"""Genera un informe semanal para {team_name}.

CONTEXTO:
{_format_context(context, lang)}

ESTRUCTURA REQUERIDA (JSON):
{{
    "headline": "Titular atractivo del informe (1 frase)",
    "sections": [
        {{
            "title": "{titles['this_week'].format(team=team_name)}",
            "content": "Resumen de la semana: resultados, dinámica, historia"
        }},
        {{
            "title": "{titles['stats']}",
            "content": "Análisis de estadísticas con interpretación (xG, tiros, posesión, tendencias)"
        }},
        {{
            "title": "{titles['key_players']}",
            "content": "Jugadores en forma, momentos decisivos"
        }},
        {{
            "title": "{titles['whats_next']}",
            "content": "Próximos partidos, apuestas, posibles lesiones"
        }}
    ]
}}"""
    }
    
    return {
        "system": system_prompts.get(lang, system_prompts["en"]),
        "user": user_prompts.get(lang, user_prompts["en"])
    }


def _format_context(context: Dict[str, Any], language: str) -> str:
    """Format the context data into a readable string for the LLM."""
    parts = []
    
    # Team info
    team_name = context.get("team_name", "Unknown")
    league = context.get("league_name", "")
    parts.append(f"Team: {team_name} ({league})")
    
    # League position
    if context.get("league_position"):
        pos = context["league_position"]
        parts.append(f"League Position: {pos.get('rank', '?')}/{pos.get('total_teams', '?')} - {pos.get('points', '?')} points")
    
    # Recent matches
    if context.get("recent_matches"):
        parts.append("\nRecent Matches:")
        for match in context["recent_matches"][:5]:  # Last 5 matches
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            score_h = match.get("score_home", "?")
            score_a = match.get("score_away", "?")
            date = match.get("date", "")
            parts.append(f"  - {home} {score_h}-{score_a} {away} ({date})")
            
            # Add stats if available
            if match.get("stats"):
                stats = match["stats"]
                stats_str = []
                if stats.get("xg_home") and stats.get("xg_away"):
                    stats_str.append(f"xG: {stats['xg_home']}-{stats['xg_away']}")
                if stats.get("possession_home"):
                    stats_str.append(f"Possession: {stats['possession_home']}")
                if stats_str:
                    parts.append(f"    Stats: {', '.join(stats_str)}")
    
    # Form
    if context.get("form"):
        parts.append(f"\nRecent Form: {context['form']}")  # e.g., "W-W-D-L-W"
    
    # Upcoming matches
    if context.get("upcoming_matches"):
        parts.append("\nUpcoming Fixtures:")
        for match in context["upcoming_matches"][:3]:  # Next 3
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            date = match.get("date", "")
            parts.append(f"  - {home} vs {away} ({date})")
    
    return "\n".join(parts)
