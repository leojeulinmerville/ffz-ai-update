from __future__ import annotations

from html import escape
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


# ---------- Helpers de normalisation ----------

def _to_str(value: Any) -> str:
    """Convertit n'importe quoi en string safe, sans planter."""
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    try:
        return str(value).strip()
    except Exception:
        return ""


def _to_str_list(value: Any) -> List[str]:
    """Transforme une valeur en liste de strings propres."""
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            s = _to_str(item)
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        # Si jamais c'est un gros bloc de texte, on le découpe par lignes.
        return [s.strip() for s in value.splitlines() if s.strip()]
    return []


# ---------- Localisation EN / FR ----------

def _get_language_labels(language: str) -> Dict[str, str]:
    lang = (language or "").lower()
    if lang.startswith("fr"):
        return {
            "subject_team": "Votre mise à jour Football Fan Zone – {team} & dernières ligues",
            "subject_default": "Votre mise à jour Football Fan Zone de la semaine",
            "greeting": "Bonjour",
            "watchlist": "Points à surveiller",
            "sources": "Sources",
            "closing": "À la semaine prochaine,",
            "table_title": "Classement (top {n}) :",
            "fan_zone_title": "Fan Zone - {team}",
            "recent_stories": "Dernières actualités",
            "table_header_rank": "#",
            "table_header_team": "Équipe",
            "table_header_points": "Pts",
            "table_header_goal_diff": "Diff",
            "table_header_played": "MJ",
            "points_abbrev": "pts",
            "matches_word": "matchs",
            "goal_diff_label": "Diff",
        }
    return {
        "subject_team": "Your Football Fan Zone update – {team} & latest leagues",
        "subject_default": "Your Football Fan Zone weekly update",
        "greeting": "Hi",
        "watchlist": "Watchlist",
        "sources": "Sources",
        "closing": "See you next week,",
        "table_title": "League table (top {n}):",
        "fan_zone_title": "Fan Zone - {team}",
        "recent_stories": "Recent stories",
        "table_header_rank": "#",
        "table_header_team": "Team",
        "table_header_points": "Pts",
        "table_header_goal_diff": "GD",
        "table_header_played": "MP",
        "points_abbrev": "pts",
        "matches_word": "matches",
        "goal_diff_label": "GD",
    }


def _build_subject(language: str, favorite_team: str | None, labels: Dict[str, str]) -> str:
    team = (favorite_team or "").strip()
    if team:
        return labels["subject_team"].format(team=team)
    return labels["subject_default"]


# ---------- Utils sortie ----------

def _unique_domains(sources: List[str]) -> List[str]:
    seen: set[str] = set()
    domains: List[str] = []
    for src in sources:
        src_str = _to_str(src)
        if not src_str:
            continue
        try:
            parsed = urlparse(src_str)
            domain = parsed.netloc or src_str
        except Exception:
            domain = src_str
        domain = domain.replace("www.", "")
        if domain and domain not in seen:
            seen.add(domain)
            domains.append(domain)
    return sorted(domains)


def _format_table_row_text(row: Dict[str, Any], labels: Dict[str, str]) -> str:
    rank = row.get("rank")
    team = _to_str(row.get("team")) or "-"
    points = row.get("points")
    points_text = f"{points} {labels['points_abbrev']}" if points is not None else "-"
    goal_diff = row.get("goal_diff")
    gd_text = f"{goal_diff:+d}" if isinstance(goal_diff, int) else "-"
    played = row.get("played")
    matches_word = labels["matches_word"]
    prefix = f"{rank or '-'}."
    if labels["greeting"].lower().startswith("bonjour"):
        matches_phrase = f"{played} {matches_word}" if played is not None else ""
        suffix = f" en {matches_phrase}" if matches_phrase else ""
        return f"{prefix} {team} – {points_text} ({gd_text}){suffix}".strip()
    matches_phrase = f"in {played} {matches_word}" if played is not None else ""
    return f"{prefix} {team} – {points_text} ({gd_text}) {matches_phrase}".strip()


# ---------- Corps texte ----------

def _build_text_body(payload: Dict[str, Any], greeting: str, labels: Dict[str, str]) -> str:
    lines: List[str] = [greeting]

    leagues = payload.get("leagues") or []
    for league in leagues:
        league_name = _to_str(league.get("league_name") or league.get("league_code") or "League")
        article = league.get("article") or {}

        lines.append("")
        lines.append(f"=== {league_name} ===")

        headline = _to_str(article.get("headline"))
        if headline:
            lines.append(headline)

        narrative = _to_str(article.get("narrative"))
        paragraphs = [p.strip() for p in narrative.split("\n\n") if p.strip()]

        table_rows = article.get("table") or []
        if table_rows:
            lines.append("")
            lines.append(labels["table_title"].format(n=len(table_rows)))
            for row in table_rows:
                lines.append(_format_table_row_text(row, labels))

        fan_zone = article.get("fan_zone") or {}
        fan_team = _to_str(fan_zone.get("team"))
        if fan_team:
            summary = _to_str(fan_zone.get("summary"))
            lines.append("")
            lines.append(labels["fan_zone_title"].format(team=fan_team))
            if summary:
                lines.append(summary)
            recent = fan_zone.get("recent_news") or []
            if recent:
                lines.append(f"{labels['recent_stories']}:")
                for item in recent:
                    title = _to_str(item.get("title"))
                    if not title:
                        continue
                    source = _to_str(item.get("source")) or "source"
                    lines.append(f"- \"{title}\" ({source})")

        if paragraphs:
            lines.append("")
            for paragraph in paragraphs:
                lines.append(paragraph)

        watchlist = _to_str_list(article.get("watchlist"))
        if watchlist:
            lines.append("")
            lines.append(f"{labels['watchlist']}:")
            for item in watchlist:
                lines.append(f"- {item}")

    domains = _unique_domains(payload.get("sources_used") or [])
    if domains:
        lines.append("")
        lines.append(f"{labels['sources']}:")
        for domain in domains:
            lines.append(f"- {domain}")

    lines.append("")
    lines.append(labels["closing"])
    lines.append("Football Fan Zone")

    return "\n".join(line for line in lines if line is not None).strip()


# ---------- Corps HTML ----------

def _build_html_body(payload: Dict[str, Any], greeting: str, labels: Dict[str, str]) -> str:
    parts: List[str] = [f"<p>{greeting}</p>"]

    leagues = payload.get("leagues") or []
    for league in leagues:
        league_name = _to_str(league.get("league_name") or league.get("league_code") or "League")
        article = league.get("article") or {}

        parts.append(f"<h2>{escape(league_name)}</h2>")

        headline = _to_str(article.get("headline"))
        if headline:
            parts.append(f"<p><strong>{escape(headline)}</strong></p>")

        table_rows = article.get("table") or []
        if table_rows:
            parts.append(f"<p><strong>{escape(labels['table_title'].format(n=len(table_rows)))}</strong></p>")
            parts.append(
                "<table><thead><tr>"
                f"<th>{escape(labels['table_header_rank'])}</th>"
                f"<th>{escape(labels['table_header_team'])}</th>"
                f"<th>{escape(labels['table_header_points'])}</th>"
                f"<th>{escape(labels['table_header_goal_diff'])}</th>"
                f"<th>{escape(labels['table_header_played'])}</th>"
                "</tr></thead><tbody>"
            )
            for row in table_rows:
                rank = row.get("rank") or ""
                team = escape(_to_str(row.get("team")) or "")
                points = row.get("points")
                goal_diff = row.get("goal_diff")
                played = row.get("played")
                parts.append(
                    "<tr>"
                    f"<td>{rank}</td>"
                    f"<td>{team}</td>"
                    f"<td>{'' if points is None else points}</td>"
                    f"<td>{'' if goal_diff is None else goal_diff}</td>"
                    f"<td>{'' if played is None else played}</td>"
                    "</tr>"
                )
            parts.append("</tbody></table>")

        narrative = _to_str(article.get("narrative"))
        paragraphs = [p.strip() for p in narrative.split("\n\n") if p.strip()]
        for paragraph in paragraphs:
            parts.append(f"<p>{escape(paragraph)}</p>")

        fan_zone = article.get("fan_zone") or {}
        fan_team = _to_str(fan_zone.get("team"))
        if fan_team:
            summary = _to_str(fan_zone.get("summary"))
            parts.append(f"<p><strong>{escape(labels['fan_zone_title'].format(team=fan_team))}</strong></p>")
            if summary:
                parts.append(f"<p>{escape(summary)}</p>")
            recent = fan_zone.get("recent_news") or []
            if recent:
                parts.append(f"<p><strong>{escape(labels['recent_stories'])}:</strong></p>")
                parts.append("<ul>")
                for item in recent:
                    title = _to_str(item.get("title"))
                    if not title:
                        continue
                    source = _to_str(item.get("source")) or "source"
                    parts.append(f"<li>&ldquo;{escape(title)}&rdquo; ({escape(source)})</li>")
                parts.append("</ul>")

        watchlist = _to_str_list(article.get("watchlist"))
        if watchlist:
            parts.append(f"<p><strong>{labels['watchlist']}:</strong></p>")
            parts.append("<ul>")
            for item in watchlist:
                parts.append(f"<li>{escape(item)}</li>")
            parts.append("</ul>")

    domains = _unique_domains(payload.get("sources_used") or [])
    if domains:
        parts.append(f"<p><strong>{labels['sources']}:</strong></p>")
        parts.append("<ul>")
        for domain in domains:
            parts.append(f"<li>{escape(domain)}</li>")
        parts.append("</ul>")

    parts.append(f"<p>{labels['closing']}<br/>Football Fan Zone</p>")
    return "\n".join(parts)


# ---------- Entrée principale ----------

def format_weekly_report_email(payload: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Utilisé par /admin/send_latest_email.
    Renvoie: (subject, text_body, html_body)
    """
    user = payload.get("user", {}) or {}
    language = _to_str(user.get("language") or "en").lower()
    labels = _get_language_labels(language)

    favorite_team = _to_str(user.get("favorite_team"))
    subject = _build_subject(language, favorite_team, labels)

    first_name = _to_str(user.get("first_name"))
    if first_name:
        greeting = f"{labels['greeting']} {first_name},"
    else:
        greeting = f"{labels['greeting']},"

    text_body = _build_text_body(payload, greeting, labels)
    html_body = _build_html_body(payload, greeting, labels)

    return subject, text_body, html_body
