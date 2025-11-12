from typing import Any, Dict, List, Optional

_BULLET = "•"
_MAX_CHARS = 950


def format_weekly_report_text(payload: Dict[str, Any]) -> List[str]:
    """
    Assemble WhatsApp-ready chunks (each <=950 characters) from the weekly report payload.
    """
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
            return f"Football Fan Zone — Ta mise à jour pour {favorite_team}."
        return "Football Fan Zone — Ta mise à jour personnalisée."
    if favorite_team:
        return f"Football Fan Zone — Your weekly update for {favorite_team}."
    return "Football Fan Zone — Your weekly update."


def _build_outro(language: str) -> str:
    return "À la semaine prochaine. ⚽️ FFZ" if language == "fr" else "See you next week. ⚽️ FFZ"


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

    watchlist = [item.strip() for item in (article.get("watchlist") or []) if item]
    if watchlist:
        header = "À surveiller :" if language == "fr" else "Watchlist:"
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
    title = f"Focus supporters — {fan_team}" if language == "fr" else f"Fan Spotlight — {fan_team}"
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
