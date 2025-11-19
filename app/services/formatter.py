import html as _html
from typing import Any, Dict, List, Optional

_BULLET = "-"
_MAX_CHARS = 950


def format_weekly_report_text(payload: Dict[str, Any]) -> List[str]:
    """Assemble WhatsApp-ready chunks (each <= 950 chars)."""
    user = payload.get("user") or {}
    language = (user.get("language") or "fr").lower()
    favorite_team = user.get("favorite_team")
    articles = payload.get("articles") or []

    chunks: List[str] = []

    intro = _build_intro(language, favorite_team)
    if intro:
        chunks.append(intro)

    for article in articles:
        league_chunk = _build_league_chunk(article, language)
        if league_chunk:
            chunks.append(league_chunk)

        fan_chunk = _build_fan_chunk(article, language)
        if fan_chunk:
            chunks.append(fan_chunk)

    outro = _build_outro(language)
    if outro:
        chunks.append(outro)

    return [chunk for chunk in chunks if chunk]


def _build_intro(language: str, favorite_team: Optional[str]) -> str:
    if language == "fr":
        if favorite_team:
            return f"Football Fan Zone - Ta mise a jour pour {favorite_team}."
        return "Football Fan Zone - Ta mise a jour personnalisee."
    if favorite_team:
        return f"Football Fan Zone - Your weekly update for {favorite_team}."
    return "Football Fan Zone - Your weekly update."


def _build_outro(language: str) -> str:
    return "A la semaine prochaine. FFZ" if language == "fr" else "See you next week. FFZ"


def _build_league_chunk(article: Dict[str, Any], language: str) -> str:
    if not article:
        return ""

    lines: List[str] = []
    headline = (article.get("headline") or article.get("league_name") or article.get("league_code") or "").strip()
    if headline:
        lines.append(headline[:85])

    narrative = (article.get("narrative") or "").strip()
    if narrative:
        lines.append(narrative)

    watchlist = [item.strip() for item in (article.get("watchlist") or []) if item and item.strip()]
    if watchlist:
        header = "A surveiller :" if language == "fr" else "Watchlist:"
        lines.append(header)
        for item in watchlist[:2]:
            lines.append(f"{_BULLET} {item}")

    footer = _format_sources_footer(article.get("sources_used"))
    if footer:
        lines.append(footer)

    chunk = "\n".join(lines).strip()
    return _clip_to_limit(chunk)


def _build_fan_chunk(article: Dict[str, Any], language: str) -> str:
    fan_spotlight = (article.get("fan_spotlight") or "").strip()
    if not fan_spotlight:
        return ""

    facts = article.get("facts") or {}
    fan_team = facts.get("fan_team") or article.get("favorite_team") or article.get("league_name")
    title = f"Focus supporters - {fan_team}" if language == "fr" else f"Fan spotlight - {fan_team}"
    chunk = f"{title}\n{fan_spotlight}"
    return _clip_to_limit(chunk)


def _format_sources_footer(sources: Optional[List[str]]) -> str:
    if not sources:
        return ""

    labels: List[str] = []
    for url in sources:
        lower = (url or "").lower()
        if "top-scorers" in lower:
            labels.append("scorers")
        elif "scores-fixtures" in lower:
            labels.append("fixtures")
        elif "table" in lower:
            labels.append("table")

    if not labels:
        return ""

    dedup: List[str] = []
    for label in labels:
        if label not in dedup:
            dedup.append(label)

    source_label = "BBC " + " / ".join(dedup)
    return f"Sources: {source_label}"


def _clip_to_limit(text: str) -> str:
    trimmed = text.strip()
    if len(trimmed) <= _MAX_CHARS:
        return trimmed
    candidate = trimmed[:_MAX_CHARS]
    for sep in ("\n", ". ", " "):
        idx = candidate.rfind(sep)
        if idx > _MAX_CHARS * 0.6:
            return candidate[:idx].strip()
    return candidate.strip()


def format_weekly_report_email(payload: Dict[str, Any]) -> Dict[str, str]:
    """Build long-form email bodies (HTML + plain text)."""
    user = payload.get("user") or {}
    language = (user.get("language") or "fr").lower()
    favorite_team = user.get("favorite_team")
    first_name = user.get("first_name")
    articles = payload.get("articles") or []

    subject = _email_subject(language, favorite_team)
    intro = _email_intro(language, favorite_team, first_name)
    outro = _email_outro(language)

    text_lines: List[str] = [intro, ""]
    
    # HTML email avec design moderne
    html_parts: List[str] = [
        '<!DOCTYPE html>',
        '<html lang="' + language + '">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<style>',
        '  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; margin: 0; padding: 0; }',
        '  .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; }',
        '  .header { background: linear-gradient(135deg, #1a73e8 0%, #34a853 100%); color: white; padding: 30px 20px; text-align: center; }',
        '  .header h1 { margin: 0; font-size: 24px; font-weight: 600; }',
        '  .content { padding: 30px 20px; }',
        '  .intro { font-size: 18px; color: #1a73e8; margin-bottom: 25px; font-weight: 500; }',
        '  .league-card { background: #ffffff; border-left: 4px solid #1a73e8; border-radius: 8px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
        '  .league-card h2 { margin-top: 0; color: #1a73e8; font-size: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }',
        '  .narrative { color: #555; margin: 15px 0; line-height: 1.8; }',
        '  .fan-spotlight { background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 6px; padding: 15px; margin: 20px 0; }',
        '  .fan-spotlight strong { color: #856404; display: block; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }',
        '  .watchlist { background: #e7f3ff; border-radius: 6px; padding: 15px; margin: 15px 0; }',
        '  .watchlist strong { color: #1a73e8; display: block; margin-bottom: 10px; }',
        '  .watchlist ul { margin: 0; padding-left: 20px; }',
        '  .watchlist li { margin: 8px 0; color: #555; }',
        '  .sources { font-size: 12px; color: #999; margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }',
        '  .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; border-top: 1px solid #eee; }',
        '  .divider { height: 1px; background: #eee; margin: 30px 0; }',
        '  @media only screen and (max-width: 600px) {',
        '    .container { width: 100% !important; }',
        '    .content { padding: 20px 15px; }',
        '  }',
        '</style>',
        '</head>',
        '<body>',
        '<div class="container">',
        '<div class="header">',
        '<h1>⚽ Football Fan Zone</h1>',
        '</div>',
        '<div class="content">',
        f'<div class="intro">{_esc(intro)}</div>',
    ]

    fan_summary = _build_fan_summary_section(payload, language)
    if fan_summary:
        text_lines.extend([fan_summary["plain"], ""])
        html_parts.append(f'<div class="fan-spotlight"><strong>{_fan_label(language)}</strong><p>{_esc(fan_summary["plain"])}</p></div>')

    if not articles:
        placeholder = (
            "Nous n'avons pas encore de rapport pour toi - genere-en un depuis l'admin."
            if language == "fr"
            else "No report available yet - generate one from the admin console."
        )
        text_lines.append(placeholder)
        html_parts.append(f'<p>{_esc(placeholder)}</p>')
    else:
        for idx, article in enumerate(articles, start=1):
            section = _normalize_article(article, language)
            section_lines = [
                section["title"],
                section["narrative"],
            ]
            # Add key moments if available
            if section.get("key_moments"):
                key_moments_label = "Moments clés" if language == "fr" else "Key Moments"
                section_lines.append(key_moments_label)
                for moment in section["key_moments"]:
                    section_lines.append(f"- {moment}")
                section_lines.append("")
            section_lines.extend([
                section["fan_spotlight_text"],
                section["watchlist_text"],
                section["sources"],
                "",
            ])
            text_lines.extend(part for part in section_lines if part)

            html_parts.append('<div class="league-card">')
            html_parts.append(f'<h2>{_esc(section["title"])}</h2>')
            if section["narrative"]:
                html_parts.append(f'<div class="narrative">{_esc(section["narrative"])}</div>')
            
            # Key moments (new field)
            if section.get("key_moments"):
                key_moments_label = "Moments clés" if language == "fr" else "Key Moments"
                html_parts.append(f'<div class="watchlist"><strong>{key_moments_label}</strong>')
                html_parts.append("<ul>" + "".join(f'<li>{_esc(item)}</li>' for item in section["key_moments"]) + "</ul></div>")
            
            # Fan spotlight: handle both old (string) and new (object) formats
            if section["fan_spotlight"]:
                if section.get("fan_analysis"):
                    # New format: structured object
                    html_parts.append(f'<div class="fan-spotlight"><strong>{_fan_label(language)}</strong>')
                    if section["fan_analysis"]:
                        html_parts.append(f'<p><strong>Analyse:</strong> {_esc(section["fan_analysis"])}</p>')
                    if section["fan_preview"]:
                        html_parts.append(f'<p><strong>{"Prochain match" if language == "fr" else "Next Match"}:</strong> {_esc(section["fan_preview"])}</p>')
                    if section["fan_tactical"]:
                        html_parts.append(f'<p><strong>{"Tactique" if language == "fr" else "Tactics"}:</strong> {_esc(section["fan_tactical"])}</p>')
                    html_parts.append("</div>")
                else:
                    # Old format: simple string
                    html_parts.append(
                        f'<div class="fan-spotlight"><strong>{_fan_label(language)}</strong><p>{_esc(section["fan_spotlight"])}</p></div>'
                    )
            
            if section["watchlist_items"]:
                html_parts.append(f'<div class="watchlist"><strong>{_watchlist_label(language)}</strong>')
                html_parts.append("<ul>" + "".join(f'<li>{_esc(item)}</li>' for item in section["watchlist_items"]) + "</ul></div>")
            if section["sources"]:
                html_parts.append(f'<div class="sources">{_esc(section["sources"])}</div>')
            html_parts.append("</div>")
            
            if idx < len(articles):
                text_lines.append("")
                html_parts.append('<div class="divider"></div>')

    text_lines.append(outro)
    html_parts.extend([
        f'<div class="footer">{_esc(outro)}</div>',
        '</div>',
        '</div>',
        '</body>',
        '</html>',
    ])

    return {
        "subject": subject,
        "plain": "\n".join(text_lines).strip(),
        "html": "\n".join(html_parts).strip(),
    }


def _normalize_article(article: Dict[str, Any], language: str) -> Dict[str, Any]:
    title = (
        (article.get("headline") or "").strip()
        or (article.get("league_name") or "").strip()
        or article.get("league_code")
        or "Weekly spotlight"
    )
    narrative = (article.get("narrative") or article.get("text") or "").strip()
    
    # Handle fan_spotlight: can be string (old format) or object (new format)
    fan_spotlight_raw = article.get("fan_spotlight")
    fan = ""
    fan_analysis = ""
    fan_preview = ""
    fan_tactical = ""
    
    if fan_spotlight_raw:
        if isinstance(fan_spotlight_raw, dict):
            # New format: object
            fan_analysis = (fan_spotlight_raw.get("analysis") or "").strip()
            fan_preview = (fan_spotlight_raw.get("next_match_preview") or "").strip()
            fan_tactical = (fan_spotlight_raw.get("tactical_notes") or "").strip()
            # Combine for text version
            fan_parts = [p for p in [fan_analysis, fan_preview, fan_tactical] if p]
            fan = " ".join(fan_parts)
        else:
            # Old format: string
            fan = str(fan_spotlight_raw).strip()
    
    # Handle key_moments (new field)
    key_moments = article.get("key_moments") or []
    if key_moments and isinstance(key_moments, list):
        key_moments = [str(m).strip() for m in key_moments if m and str(m).strip()]
    
    watchlist_items = [item.strip() for item in (article.get("watchlist") or []) if item and item.strip()]
    watchlist_text = ""
    if watchlist_items:
        label = _watchlist_label(language)
        watchlist_text = "\n".join([label] + [f"- {item}" for item in watchlist_items])
    sources = _format_sources_footer(article.get("sources_used"))
    # Build fan_spotlight_text for plain text version
    fan_spotlight_text = ""
    if fan:
        if fan_analysis or fan_preview or fan_tactical:
            # New format: combine all parts
            fan_parts = []
            if fan_analysis:
                fan_parts.append(fan_analysis)
            if fan_preview:
                fan_parts.append(fan_preview)
            if fan_tactical:
                fan_parts.append(fan_tactical)
            fan_spotlight_text = f"{_fan_label(language)} : {' '.join(fan_parts)}"
        else:
            # Old format: simple string
            fan_spotlight_text = f"{_fan_label(language)} : {fan}"
    
    return {
        "title": title,
        "narrative": narrative,
        "fan_spotlight": fan,
        "fan_spotlight_text": fan_spotlight_text,
        "fan_analysis": fan_analysis,
        "fan_preview": fan_preview,
        "fan_tactical": fan_tactical,
        "key_moments": key_moments,
        "watchlist_items": watchlist_items,
        "watchlist_text": watchlist_text,
        "sources": sources,
    }


def _build_fan_summary_section(payload: Dict[str, Any], language: str) -> Optional[Dict[str, str]]:
    user = payload.get("user") or {}
    favorite_team = (user.get("favorite_team") or "").strip()
    if not favorite_team:
        return None

    articles = payload.get("articles") or []
    chosen_facts: Optional[Dict[str, Any]] = None
    for article in articles:
        facts = article.get("facts") or {}
        fan_team = (facts.get("fan_team") or "").strip()
        if fan_team and fan_team.lower() == favorite_team.lower():
            chosen_facts = facts
            break
        table = facts.get("table") or []
        if table and any((row.get("team") or "").lower() == favorite_team.lower() for row in table):
            chosen_facts = facts
            break

    if not chosen_facts:
        return None

    plain = _render_fan_summary_plain(favorite_team, chosen_facts, language)
    html = f"<p><strong>{_fan_label(language)} - {_esc(favorite_team)}</strong></p><p>{_esc(plain)}</p>"
    return {"plain": plain, "html": html}


def _render_fan_summary_plain(favorite_team: str, facts: Dict[str, Any], language: str) -> str:
    lines: List[str] = []
    table = facts.get("table") or []
    favorite_row = None
    for row in table:
        if (row.get("team") or "").lower() == favorite_team.lower():
            favorite_row = row
            break

    if favorite_row:
        rank = favorite_row.get("rank")
        points = favorite_row.get("points")
        if language == "fr":
            lines.append(f"{favorite_team} occupe la position {rank} avec {points} point(s).")
        else:
            lines.append(f"{favorite_team} sit in position {rank} with {points} point(s).")

    next_match = facts.get("next_match") or {}
    if next_match and next_match.get("home") and next_match.get("away"):
        opponent = next_match["away"] if next_match["home"].lower() == favorite_team.lower() else next_match["home"]
        kickoff = next_match.get("local_kickoff") or next_match.get("utc_kickoff")
        if language == "fr":
            snippet = f"Prochain match contre {opponent}"
            if kickoff:
                snippet += f" ({kickoff})"
            lines.append(snippet + ".")
        else:
            snippet = f"Next up against {opponent}"
            if kickoff:
                snippet += f" ({kickoff})"
            lines.append(snippet + ".")

    tight_gaps = facts.get("tight_gaps") or []
    if tight_gaps and len(table) >= 2:
        gap = tight_gaps[0]
        diff = gap.get("gap_points")
        if diff is not None:
            pos1 = gap.get("pos1", 1) - 1
            pos2 = gap.get("pos2", 2) - 1
            team1 = table[pos1].get("team") if pos1 < len(table) else None
            team2 = table[pos2].get("team") if pos2 < len(table) else None
            if team1 and team2:
                if language == "fr":
                    lines.append(f"L'ecart n'est que de {diff} point(s) entre {team1} et {team2}.")
                else:
                    lines.append(f"Only {diff} point(s) separate {team1} and {team2}.")

    if not lines:
        lines.append(
            "Toujours a l'affut, continue de suivre leur evolution."
            if language == "fr"
            else "Keep following their form for more details next week."
        )

    return " ".join(lines)


def _email_subject(language: str, favorite_team: Optional[str]) -> str:
    base = "FFZ - Ta mise a jour" if language == "fr" else "FFZ - Your weekly update"
    if favorite_team:
        return f"{base} | {favorite_team}"
    return base


def _email_intro(language: str, favorite_team: Optional[str], first_name: Optional[str] = None) -> str:
    if language == "fr":
        if first_name:
            if favorite_team:
                return f"Salut {first_name} ! Voici ce qu'il faut retenir pour {favorite_team}."
            return f"Salut {first_name} ! Voici ta dose hebdomadaire signée Football Fan Zone."
        if favorite_team:
            return f"Salut ! Voici ce qu'il faut retenir pour {favorite_team}."
        return "Salut ! Voici ta dose hebdomadaire signée Football Fan Zone."
    if first_name:
        if favorite_team:
            return f"Hey {first_name}! Here's what's new for {favorite_team}."
        return f"Hey {first_name}! Here's your Football Fan Zone weekly digest."
    if favorite_team:
        return f"Hey! Here's what's new for {favorite_team}."
    return "Hey! Here's your Football Fan Zone weekly digest."


def _email_outro(language: str) -> str:
    return "A tres vite - L'equipe Football Fan Zone." if language == "fr" else "Talk soon - The Football Fan Zone team."


def _watchlist_label(language: str) -> str:
    return "A surveiller :" if language == "fr" else "Watchlist:"


def _fan_label(language: str) -> str:
    return "Focus supporters" if language == "fr" else "Fan spotlight"


def _esc(value: str) -> str:
    return _html.escape(value or "", quote=False)
