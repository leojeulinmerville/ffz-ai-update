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
    articles = payload.get("articles") or []

    subject = _email_subject(language, favorite_team)
    intro = _email_intro(language, favorite_team)
    outro = _email_outro(language)

    text_lines: List[str] = [intro, ""]
    html_parts: List[str] = [f"<p>{_esc(intro)}</p>"]

    fan_summary = _build_fan_summary_section(payload, language)
    if fan_summary:
        text_lines.extend([fan_summary["plain"], ""])
        html_parts.append(fan_summary["html"])

    if not articles:
        placeholder = (
            "Nous n'avons pas encore de rapport pour toi - genere-en un depuis l'admin."
            if language == "fr"
            else "No report available yet - generate one from the admin console."
        )
        text_lines.append(placeholder)
        html_parts.append(f"<p>{_esc(placeholder)}</p>")
    else:
        for idx, article in enumerate(articles, start=1):
            section = _normalize_article(article, language)
            section_lines = [
                section["title"],
                section["narrative"],
                section["fan_spotlight_text"],
                section["watchlist_text"],
                section["sources"],
                "",
            ]
            text_lines.extend(part for part in section_lines if part)

            html_parts.append(f"<h2>{_esc(section['title'])}</h2>")
            if section["narrative"]:
                html_parts.append(f"<p>{_esc(section['narrative'])}</p>")
            if section["fan_spotlight"]:
                html_parts.append(
                    f"<p><strong>{_fan_label(language)}:</strong> {_esc(section['fan_spotlight'])}</p>"
                )
            if section["watchlist_items"]:
                html_parts.append(f"<p><strong>{_watchlist_label(language)}</strong></p>")
                html_parts.append(
                    "<ul>" + "".join(f"<li>{_esc(item)}</li>" for item in section["watchlist_items"]) + "</ul>"
                )
            if section["sources"]:
                html_parts.append(f"<p class=\"sources\">{_esc(section['sources'])}</p>")
            if idx < len(articles):
                text_lines.append("")
                html_parts.append("<hr />")

    text_lines.append(outro)
    html_parts.append(f"<p>{_esc(outro)}</p>")

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
    fan = (article.get("fan_spotlight") or "").strip()
    watchlist_items = [item.strip() for item in (article.get("watchlist") or []) if item and item.strip()]
    watchlist_text = ""
    if watchlist_items:
        label = _watchlist_label(language)
        watchlist_text = "\n".join([label] + [f"- {item}" for item in watchlist_items])
    sources = _format_sources_footer(article.get("sources_used"))
    return {
        "title": title,
        "narrative": narrative,
        "fan_spotlight": fan,
        "fan_spotlight_text": f"{_fan_label(language)} : {fan}" if fan else "",
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


def _email_intro(language: str, favorite_team: Optional[str]) -> str:
    if language == "fr":
        if favorite_team:
            return f"Salut ! Voici ce qu'il faut retenir pour {favorite_team}."
        return "Salut ! Voici ta dose hebdomadaire signee Football Fan Zone."
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
