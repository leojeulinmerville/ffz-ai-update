"""
Email formatter for FFZ reports

Formats generated reports into professional HTML emails
"""

import html as _html
from typing import Dict, Any


def format_report_email(report_payload: Dict[str, Any], user_email: str, user_name: str = None) -> Dict[str, str]:
    """
    Format a generated report into HTML and plain text email.
    
    Args:
        report_payload: The report dict from report_generator
        user_email: Recipient email
        user_name: Optional user first name
        
    Returns:
        Dict with 'subject', 'html', 'plain'
    """
    headline = report_payload.get("headline", "Your Weekly Football Report")
    sections = report_payload.get("sections", [])
    team_name = report_payload.get("team_name", "your team")
    language = report_payload.get("language", "en")
    
    # Subject
    subject = _get_subject(team_name, language)
    
    # Greeting
    greeting = _get_greeting(user_name, team_name, language)
    
    # Build plain text
    plain_parts = [greeting, ""]
    plain_parts.append(headline)
    plain_parts.append("")
    
    for section in sections:
        plain_parts.append(f"## {section.get('title', '')}")
        plain_parts.append(section.get('content', ''))
        plain_parts.append("")
    
    plain_parts.append(_get_footer(language))
    
    # Build HTML
    html = _build_html_email(headline, sections, greeting, language, user_email)
    
    return {
        "subject": subject,
        "html": html,
        "plain": "\n".join(plain_parts)
    }


def _get_subject(team_name: str, language: str) -> str:
    """Get email subject line"""
    if language == "fr":
        return f"⚽ FFZ - Votre rapport hebdomadaire | {team_name}"
    elif language == "es":
        return f"⚽ FFZ - Tu informe semanal | {team_name}"
    else:
        return f"⚽ FFZ - Your Weekly Report | {team_name}"


def _get_greeting(user_name: str, team_name: str, language: str) -> str:
    """Get email greeting"""
    if language == "fr":
        if user_name:
            return f"Salut {user_name} ! Voici votre rapport hebdomadaire pour {team_name}."
        return f"Salut ! Voici votre rapport hebdomadaire pour {team_name}."
    elif language == "es":
        if user_name:
            return f"¡Hola {user_name}! Aquí está tu informe semanal para {team_name}."
        return f"¡Hola! Aquí está tu informe semanal para {team_name}."
    else:
        if user_name:
            return f"Hey {user_name}! Here's your weekly report for {team_name}."
        return f"Hey! Here's your weekly report for {team_name}."


def _get_footer(language: str) -> str:
    """Get email footer"""
    if language == "fr":
        return "À la semaine prochaine !\n\nL'équipe Football Fan Zone\n\nVous ne souhaitez plus recevoir ces emails ? Gérez vos préférences dans votre compte."
    elif language == "es":
        return "¡Hasta la próxima semana!\n\nEl equipo de Football Fan Zone\n\n¿No quieres recibir más estos correos? Gestiona tus preferencias en tu cuenta."
    else:
        return "See you next week!\n\nThe Football Fan Zone Team\n\nDon't want to receive these emails? Manage your preferences in your account."


def _build_html_email(headline: str, sections: list, greeting: str, language: str, user_email: str) -> str:
    """Build responsive HTML email"""
    
    # Build sections HTML
    sections_html = []
    for section in sections:
        title = _esc(section.get('title', ''))
        content = _esc(section.get('content', '')).replace('\n', '<br>')
        
        sections_html.append(f'''
        <div class="section">
            <h2>{title}</h2>
            <div class="content">{content}</div>
        </div>
        ''')
    
    sections_str = '\n'.join(sections_html)
    
    # Unsubscribe link
    unsubscribe_text = {
        "fr": "Se désabonner",
        "es": "Darse de baja",
        "en": "Unsubscribe"
    }.get(language, "Unsubscribe")
    
    html = f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #1a73e8 0%, #34a853 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .greeting {{
            padding: 30px;
            font-size: 18px;
            color: #1a73e8;
            font-weight: 500;
            border-bottom: 2px solid #f0f0f0;
        }}
        .headline {{
            padding: 30px;
            font-size: 24px;
            font-weight: 600;
            color: #1a1a1a;
            text-align: center;
            background: #f8f9fa;
        }}
        .section {{
            padding: 30px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .section:last-of-type {{
            border-bottom: none;
        }}
        .section h2 {{
            color: #1a73e8;
            font-size: 20px;
            margin-top: 0;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .section .content {{
            color: #555;
            line-height: 1.8;
            font-size: 16px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
            border-top: 2px solid #e0e0e0;
        }}
        .footer p {{
            margin: 10px 0;
        }}
        .footer a {{
            color: #1a73e8;
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        @media only screen and (max-width: 600px) {{
            .container {{
                margin: 0;
                border-radius: 0;
            }}
            .header, .greeting, .headline, .section, .footer {{
                padding: 20px;
            }}
            .headline {{
                font-size: 20px;
            }}
            .section h2 {{
                font-size: 18px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚽ Football Fan Zone</h1>
        </div>
        
        <div class="greeting">
            {_esc(greeting)}
        </div>
        
        <div class="headline">
            {_esc(headline)}
        </div>
        
        {sections_str}
        
        <div class="footer">
            <p>{_esc(_get_footer(language))}</p>
            <p style="margin-top: 20px;">
                <a href="http://127.0.0.1:8000/dashboard">{unsubscribe_text}</a>
            </p>
        </div>
    </div>
</body>
</html>'''
    
    return html


def _esc(value: str) -> str:
    """HTML escape"""
    return _html.escape(value or "", quote=False)
