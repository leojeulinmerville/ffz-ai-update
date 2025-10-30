from typing import Any, Dict, List


def format_weekly_report_text(payload: Dict[str, Any]) -> str:
    """
    Serialize a stored weekly report payload into a plain-text message body.
    """
    articles: List[Dict[str, Any]] = payload.get("articles") or []
    lines: List[str] = []

    for article in articles:
        league_name = article.get("league_name") or article.get("league_code") or "League"
        text = article.get("text") or ""

        lines.append(f"{league_name} \u2014")
        lines.append(text.rstrip())
        lines.append("")

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)
