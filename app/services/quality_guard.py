import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

PARIS_TZ = ZoneInfo("Europe/Paris")
BANNED_MARKDOWN = re.compile(r"[*_~`]")
WHITESPACE_RE = re.compile(r"\s+")

WATCHLIST_MAX_CHARS = 80
NARRATIVE_TARGET_MIN = 450
NARRATIVE_TARGET_MAX = 700
NARRATIVE_HARD_MIN = 350
NARRATIVE_HARD_MAX = 750
FAN_MIN = 350
FAN_MAX = 550

DAY_NAMES = {
    "fr": ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."],
    "en": ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."],
}

MONTH_NAMES = {
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
    "en": ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."],
}


def ensure_article(
    facts: Dict[str, Any],
    candidate: Optional[Dict[str, Any]],
    language: str,
    fan_focus: bool,
) -> Tuple[Dict[str, Any], bool]:
    sanitized_facts = _sanitize_facts(facts)
    watchlist = build_watchlist(sanitized_facts, language)

    if not _is_valid_candidate(candidate, language, fan_focus):
        return fallback_article(sanitized_facts, language, fan_focus, watchlist), True

    headline = _clean_text(candidate.get("headline", ""), language)[:100]  # Increased from 85 to 100
    narrative = _clean_text(candidate.get("narrative", ""), language)
    fan_spotlight_raw = candidate.get("fan_spotlight")
    key_moments = candidate.get("key_moments", [])
    candidate_watchlist = candidate.get("watchlist") or []

    fallback_used = False

    narrative, narrative_regen = _enforce_narrative_length(narrative, sanitized_facts, language)
    if narrative is None:
        return fallback_article(sanitized_facts, language, fan_focus, watchlist), True

    enforced_watchlist = _enforce_watchlist(candidate_watchlist, sanitized_facts, language)
    if enforced_watchlist != candidate_watchlist:
        fallback_used = True
    watchlist = enforced_watchlist

    # Handle fan_spotlight: can be string (old format) or object (new format)
    fan_spotlight = None
    if fan_focus and sanitized_facts.get("next_match"):
        if fan_spotlight_raw:
            if isinstance(fan_spotlight_raw, dict):
                # New format: object with analysis, next_match_preview, tactical_notes
                fan_spotlight = {
                    "analysis": _clean_text(fan_spotlight_raw.get("analysis", ""), language),
                    "next_match_preview": _clean_text(fan_spotlight_raw.get("next_match_preview", ""), language),
                    "tactical_notes": _clean_text(fan_spotlight_raw.get("tactical_notes", ""), language),
                }
                # Validate lengths
                if len(fan_spotlight["analysis"]) < 400 or len(fan_spotlight["analysis"]) > 600:
                    fan_spotlight = _fallback_fan_spotlight_object(sanitized_facts, language)
            else:
                # Old format: string
                cleaned = _clean_text(str(fan_spotlight_raw), language)
                fan_spotlight_str = _enforce_fan_spotlight_length(cleaned, sanitized_facts, language)
                if fan_spotlight_str:
                    # Convert old format to new format for consistency
                    fan_spotlight = {
                        "analysis": fan_spotlight_str,
                        "next_match_preview": "",
                        "tactical_notes": "",
                    }
        else:
            fan_spotlight = _fallback_fan_spotlight_object(sanitized_facts, language)
    
    # Process key_moments if present
    processed_key_moments = []
    if key_moments and isinstance(key_moments, list):
        for moment in key_moments[:2]:
            if isinstance(moment, str) and moment.strip():
                cleaned = _clean_text(moment, language)
                if 80 <= len(cleaned) <= 120:
                    processed_key_moments.append(cleaned)

    return (
        {
            "league_code": sanitized_facts.get("league_code"),
            "headline": headline or (sanitized_facts.get("league_name") or ""),
            "narrative": narrative,
            "key_moments": processed_key_moments if processed_key_moments else None,
            "watchlist": watchlist,
            "fan_spotlight": fan_spotlight,
        },
        fallback_used or narrative_regen,
    )


def build_watchlist(facts: Dict[str, Any], language: str) -> List[str]:
    bullets: List[str] = []

    top5 = facts.get("top5") or []
    tight_gaps = facts.get("tight_gaps") or []
    duels = facts.get("top5_duels_this_week") or []
    calendar_notes = facts.get("calendar_notes") or []
    next_match = facts.get("next_match") or {}

    if tight_gaps and len(top5) >= 2:
        gap = tight_gaps[0]
        idx1 = min(len(top5), gap.get("pos1", 1)) - 1
        idx2 = min(len(top5), gap.get("pos2", 2)) - 1
        team1 = top5[idx1].get("club")
        team2 = top5[idx2].get("club")
        diff = gap.get("gap_points")
        if team1 and team2 and diff is not None:
            if language == "fr":
                bullets.append(f"L'écart n'est que de {diff} point(s) entre {team1} et {team2}.")
            else:
                bullets.append(f"Only {diff} point(s) separate {team1} and {team2}.")

    if duels:
        clash = duels[0]
        kickoff = _format_paris_datetime(
            clash.get("date_paris") or clash.get("date_utc"),
            language,
        )
        home = clash.get("home")
        away = clash.get("away")
        if home and away and kickoff:
            if language == "fr":
                bullets.append(f"Choc du top 5 : {home} - {away} ({kickoff}).")
            else:
                bullets.append(f"Top-five showdown: {home} vs {away} ({kickoff}).")

    if len(bullets) < 2 and calendar_notes:
        note = calendar_notes[0]
        if isinstance(note, dict):
            team = note.get("team")
            matches = note.get("matches")
            if team and matches:
                if language == "fr":
                    bullets.append(f"{team} doit enchaîner {matches} matchs en 7 jours.")
                else:
                    bullets.append(f"{team} faces {matches} matches in 7 days.")
        elif isinstance(note, str):
            bullets.append(note)

    if len(bullets) < 2 and next_match.get("home") and next_match.get("away"):
        kickoff = _format_paris_datetime(
            next_match.get("local_kickoff") or next_match.get("paris_kickoff") or next_match.get("utc_kickoff"),
            language,
        )
        if language == "fr":
            bullets.append(
                f"Prochain rendez-vous : {next_match['home']} - {next_match['away']}{' (' + kickoff + ')' if kickoff else ''}."
            )
        else:
            bullets.append(
                f"Next test: {next_match['home']} vs {next_match['away']}{' (' + kickoff + ')' if kickoff else ''}."
            )

    while len(bullets) < 2:
        bullets.append(_generic_watchlist_line(len(bullets), language))

    trimmed = [_truncate_line(line) for line in bullets[:2]]
    return trimmed


def fallback_article(
    facts: Dict[str, Any],
    language: str,
    fan_focus: bool,
    watchlist: Optional[List[str]] = None,
) -> Dict[str, Any]:
    watchlist = watchlist or build_watchlist(facts, language)
    top5 = facts.get("top5") or []
    top_scorers = facts.get("top_scorers") or []
    league_name = facts.get("league_name") or facts.get("league_code")

    leader = top5[0] if top5 else {}
    runner_up = top5[1] if len(top5) > 1 else {}

    narrative = _fallback_narrative(language, league_name, leader, runner_up, top_scorers, facts)
    fan_spotlight = _fallback_fan_spotlight(facts, language) if fan_focus else None

    return {
        "league_code": facts.get("league_code"),
        "headline": _fallback_headline(language, league_name, leader, runner_up),
        "narrative": narrative,
        "watchlist": watchlist[:2],
        "fan_spotlight": fan_spotlight,
    }


def _fallback_headline(language: str, league_name: Optional[str], leader: Dict[str, Any], runner_up: Dict[str, Any]) -> str:
    league = league_name or "La ligue" if language == "fr" else "The league"
    leader_name = leader.get("club")
    runner_name = runner_up.get("club")
    if language == "fr":
        if leader_name and runner_name:
            return f"{league} — duel entre {leader_name} et {runner_name}"
        if leader_name:
            return f"{league} — {leader_name} aux commandes"
        return f"{league} — bilan de la semaine"
    else:
        if leader_name and runner_name:
            return f"{league} — {leader_name} and {runner_name} set the pace"
        if leader_name:
            return f"{league} — {leader_name} keep control"
        return f"{league} — weekly briefing"


def _fallback_narrative(
    language: str,
    league_name: Optional[str],
    leader: Dict[str, Any],
    runner_up: Dict[str, Any],
    top_scorers: List[Dict[str, Any]],
    facts: Dict[str, Any],
) -> str:
    sentences: List[str] = []
    league = league_name or (facts.get("league_code") or "La ligue")
    leader_name = leader.get("club")
    leader_pts = leader.get("points")
    runner_name = runner_up.get("club")
    runner_pts = runner_up.get("points")

    if language == "fr":
        if leader_name and leader_pts is not None:
            sentences.append(f"{league} voit {leader_name} en tête avec {leader_pts} points.")
        if runner_name and runner_pts is not None:
            sentences.append(f"{runner_name} reste à portée avec {runner_pts} unités.")
        if facts.get("tight_gaps"):
            gap = facts["tight_gaps"][0]
            diff = gap.get("gap_points")
            if diff is not None and runner_name and leader_name:
                sentences.append(f"L'écart entre {leader_name} et {runner_name} n'est que de {diff} point(s).")
        if top_scorers:
            leader_scorer = top_scorers[0]
            sentences.append(
                f"Côté buteurs, {leader_scorer.get('player')} ({leader_scorer.get('club')}) totalise {leader_scorer.get('goals')} réalisations."
            )
        calendar_notes = facts.get("calendar_notes") or []
        if calendar_notes:
            sentences.append(calendar_notes[0])
    else:
        if leader_name and leader_pts is not None:
            sentences.append(f"{leader_name} lead {league} on {leader_pts} points.")
        if runner_name and runner_pts is not None:
            sentences.append(f"{runner_name} keep the chase alive with {runner_pts} points.")
        if facts.get("tight_gaps"):
            gap = facts["tight_gaps"][0]
            diff = gap.get("gap_points")
            if diff is not None and runner_name and leader_name:
                sentences.append(f"The gap between {leader_name} and {runner_name} is down to {diff} point(s).")
        if top_scorers:
            leader_scorer = top_scorers[0]
            player_name = leader_scorer.get("player")
            scorer_club = leader_scorer.get("club") or leader_scorer.get("team")
            club_suffix = f" ({scorer_club})" if scorer_club else ""
            sentences.append(
                f"Top scorer watch: {player_name}{club_suffix} sits on {leader_scorer.get('goals')} goals."
            )
        calendar_notes = facts.get("calendar_notes") or []
        if calendar_notes:
            sentences.append(calendar_notes[0])

    return " ".join(sentences)


def _fallback_fan_spotlight(facts: Dict[str, Any], language: str) -> Optional[str]:
    fan_team = facts.get("fan_team")
    if not fan_team:
        return None

    next_match = facts.get("next_match") or {}
    if not (next_match.get("home") and next_match.get("away")):
        return None

    opponent = next_match["away"] if next_match["home"] == fan_team else next_match["home"]
    kickoff = _format_paris_datetime(
        next_match.get("local_kickoff") or next_match.get("paris_kickoff") or next_match.get("utc_kickoff"),
        language,
    )
    tight = facts.get("tight_gaps") or []
    bullet = ""
    if tight:
        gap = tight[0].get("gap_points")
        club = tight[0].get("club_b")
        if language == "fr":
            bullet = f"Le classement reste serré : {fan_team} n'a que {gap} point(s) d'avance sur {club}."
        else:
            bullet = f"The table stays tight: {fan_team} hold a {gap}-point edge over {club}."

    scouting = (
        "Protect the half-spaces, recycle the ball after regains, and trigger a higher press once the opponent drifts wide."
        if language != "fr"
        else "Protégez les demi-espaces, recyclez le ballon après chaque récupération et déclenchez le pressing haut dès que l'adversaire s'écarte."
    )
    finishing = (
        "Switch play quickly to stretch their back line and stay calm on dead balls—one set-piece can tilt the match."
        if language != "fr"
        else "Renversez vite le jeu pour étirer leur bloc et restez lucides sur coups de pied arrêtés : un détail peut faire basculer la rencontre."
    )

    if language == "fr":
        parts = [
            f"Focus {fan_team} : prochain rendez-vous face à {opponent}{' (' + kickoff + ')' if kickoff else ''}.",
            bullet,
            scouting,
            finishing,
        ]
    else:
        parts = [
            f"Fan spotlight — {fan_team}: next up vs {opponent}{' (' + kickoff + ')' if kickoff else ''}.",
            bullet,
            scouting,
            finishing,
        ]
    text = " ".join(part for part in parts if part).strip()
    if len(text) < FAN_MIN:
        text = f"{text} {scouting} {finishing}"
    return text[:FAN_MAX] if len(text) > FAN_MAX else text


def _fallback_fan_spotlight_object(facts: Dict[str, Any], language: str) -> Optional[Dict[str, str]]:
    """Generate fallback fan spotlight in new object format."""
    fan_team = facts.get("fan_team")
    if not fan_team:
        return None

    next_match = facts.get("next_match") or {}
    if not (next_match.get("home") and next_match.get("away")):
        return None

    opponent = next_match["away"] if next_match["home"] == fan_team else next_match["home"]
    kickoff = _format_paris_datetime(
        next_match.get("local_kickoff") or next_match.get("paris_kickoff") or next_match.get("utc_kickoff"),
        language,
    )
    
    # Get evolution data if available
    fan_evolution = facts.get("fan_evolution", {})
    current_pos = fan_evolution.get("current_stats", {}).get("position") if fan_evolution else None
    position_change = fan_evolution.get("change", 0) if fan_evolution else 0
    
    if language == "fr":
        analysis = f"{fan_team} occupe actuellement la {current_pos}e position" if current_pos else f"{fan_team}"
        if position_change > 0:
            analysis += f", en hausse de {position_change} place(s)."
        elif position_change < 0:
            analysis += f", en baisse de {abs(position_change)} place(s)."
        else:
            analysis += " maintient sa position."
        
        preview = f"Prochain match face à {opponent}"
        if kickoff:
            preview += f" ({kickoff})"
        preview += ". Un match crucial pour la suite de la saison."
        
        tactical = "Surveillez les transitions rapides et la pression haute. Le contrôle du milieu sera déterminant."
    else:
        analysis = f"{fan_team} currently sit in {current_pos}th position" if current_pos else f"{fan_team}"
        if position_change > 0:
            analysis += f", up {position_change} place(s)."
        elif position_change < 0:
            analysis += f", down {abs(position_change)} place(s)."
        else:
            analysis += " maintain their position."
        
        preview = f"Next up against {opponent}"
        if kickoff:
            preview += f" ({kickoff})"
        preview += ". A crucial match for the season ahead."
        
        tactical = "Watch for quick transitions and high pressing. Midfield control will be decisive."
    
    return {
        "analysis": analysis[:600],
        "next_match_preview": preview[:300],
        "tactical_notes": tactical[:250],
    }


def _describe_form(form: List[str], language: str) -> str:
    wins = form.count("W")
    draws = form.count("D")
    losses = form.count("L")
    if language == "fr":
        return f"{wins} victoire(s), {draws} nul(s), {losses} défaite(s) sur les dernières sorties"
    return f"{wins} win(s), {draws} draw(s), {losses} loss(es) over the recent run"


def _format_paris_datetime(utc_iso: Optional[str], language: str) -> Optional[str]:
    if not utc_iso:
        return None
    try:
        dt_utc = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)
    dt_paris = dt_utc.astimezone(PARIS_TZ)
    lang = "fr" if language == "fr" else "en"
    day = DAY_NAMES[lang][dt_paris.weekday()]
    month = MONTH_NAMES[lang][dt_paris.month - 1]
    return f"{day} {dt_paris.day} {month} {dt_paris:%H:%M}"


def _is_valid_candidate(candidate: Optional[Dict[str, Any]], language: str, fan_focus: bool) -> bool:
    if not candidate or not isinstance(candidate, dict):
        return False

    required_keys = {"league_code", "headline", "narrative", "watchlist"}
    if not required_keys.issubset(candidate.keys()):
        return False

    # Support both old format (fan_spotlight as string) and new format (fan_spotlight as object)
    watchlist = candidate.get("watchlist")
    if not isinstance(watchlist, list) or len(watchlist) < 2:
        return False

    narrative = candidate.get("narrative")
    if not isinstance(narrative, str):
        return False

    if BANNED_MARKDOWN.search(narrative or ""):
        return False

    # Check fan_spotlight: can be null, string (old format), or object (new format)
    fan_spotlight = candidate.get("fan_spotlight")
    if fan_focus is False and fan_spotlight:
        return False
    if fan_focus is True and fan_spotlight:
        # If it's an object, check it has the right structure
        if isinstance(fan_spotlight, dict):
            if not all(key in fan_spotlight for key in ["analysis", "next_match_preview", "tactical_notes"]):
                return False

    return True


def _clean_text(value: str, language: str) -> str:
    cleaned = BANNED_MARKDOWN.sub("", value or "")
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def _generic_watchlist_line(index: int, language: str) -> str:
    if language == "fr":
        return "Surveille les dynamiques du tableau." if index == 0 else "Observez les prochains matchs clés."
    return "Monitor the shifts near the top." if index == 0 else "Keep an eye on the upcoming fixtures."


def _sanitize_facts(facts: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = dict(facts)
    table = facts.get("table") or []
    table_teams = {row.get("team") for row in table if row.get("team")}
    top5 = facts.get("top5") or []
    if table_teams:
        sanitized["top5"] = [entry for entry in top5 if entry.get("club") in table_teams]
    else:
        sanitized["top5"] = top5
    return sanitized


def _enforce_narrative_length(narrative: str, facts: Dict[str, Any], language: str) -> Tuple[Optional[str], bool]:
    if not narrative:
        return _rebalance_narrative(facts, language), True

    length = len(narrative)
    if length < NARRATIVE_HARD_MIN or length > NARRATIVE_HARD_MAX:
        return _rebalance_narrative(facts, language), True
    if length > NARRATIVE_TARGET_MAX:
        return _clip_text(narrative, NARRATIVE_TARGET_MAX), True
    if length < NARRATIVE_TARGET_MIN:
        regenerated = _rebalance_narrative(facts, language)
        if regenerated:
            return regenerated, True
    return narrative, False


def _rebalance_narrative(facts: Dict[str, Any], language: str) -> Optional[str]:
    league_name = facts.get("league_name") or facts.get("league_code")
    top5 = facts.get("top5") or []
    leader = top5[0] if top5 else {}
    runner = top5[1] if len(top5) > 1 else {}
    narrative = _fallback_narrative(language, league_name, leader, runner, facts.get("top_scorers") or [], facts)
    extras = []
    tight = facts.get("tight_gaps") or []
    if tight:
        gap = tight[0].get("gap_points")
        club = tight[0].get("club_b")
        if language == "fr":
            extras.append(f"L'écart reste minimal avec {club}: seulement {gap} point(s) d'avance.")
        else:
            extras.append(f"The gap to {club} remains minimal at just {gap} point(s).")
    scorers = facts.get("top_scorers") or []
    if scorers:
        top_scorer = scorers[0]
        if language == "fr":
            extras.append(f"Au classement des buteurs, {top_scorer.get('player')} ({top_scorer.get('club')}) plane avec {top_scorer.get('goals')} réalisations.")
        else:
            extras.append(f"In the scoring charts, {top_scorer.get('player')} ({top_scorer.get('club')}) leads with {top_scorer.get('goals')} goals.")
    next_match = facts.get("next_match") or {}
    if next_match.get("home") and next_match.get("away"):
        kickoff = _format_paris_datetime(next_match.get("local_kickoff") or next_match.get("utc_kickoff"), language)
        if language == "fr":
            extras.append(f"Prochain choc: {next_match['home']} - {next_match['away']}{' (' + kickoff + ')' if kickoff else ''}.")
        else:
            extras.append(f"Next clash: {next_match['home']} vs {next_match['away']}{' (' + kickoff + ')' if kickoff else ''}.")

    for line in extras:
        if line and line not in narrative:
            narrative = f"{narrative} {line}".strip()
        if len(narrative) >= NARRATIVE_TARGET_MIN:
            break
    if len(narrative) < NARRATIVE_TARGET_MIN:
        filler = "Pressure remains intense across the table, making every possession and set piece decisive."
        if language == "fr":
            filler = "La pression demeure à chaque ligne, chaque possession et chaque coup de pied arrêté pouvant faire basculer la rencontre."
        while len(narrative) < NARRATIVE_TARGET_MIN:
            narrative = f"{narrative} {filler}".strip()
    narrative = _clip_text(narrative, NARRATIVE_TARGET_MAX)
    return narrative.strip()


def _enforce_watchlist(
    candidate_watchlist: List[str],
    facts: Dict[str, Any],
    language: str,
) -> List[str]:
    cleaned = [
        _truncate_line(_clean_text(item, language))
        for item in candidate_watchlist
        if isinstance(item, str) and item.strip()
    ]
    if len(cleaned) == 2 and all(len(item) <= WATCHLIST_MAX_CHARS for item in cleaned):
        return cleaned
    return build_watchlist(facts, language)


def _truncate_line(line: str) -> str:
    if len(line) <= WATCHLIST_MAX_CHARS:
        return line
    return _clip_text(line, WATCHLIST_MAX_CHARS)


def _clip_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text.strip()
    clipped = text[:limit].rsplit(" ", 1)[0]
    return clipped.strip()


def _enforce_fan_spotlight_length(text: Optional[str], facts: Dict[str, Any], language: str) -> Optional[str]:
    if not text:
        return _fallback_fan_spotlight(facts, language)
    length = len(text)
    if FAN_MIN <= length <= FAN_MAX:
        return text
    fallback = _fallback_fan_spotlight(facts, language)
    if fallback:
        fallback = _clip_text(fallback, FAN_MAX)
        if len(fallback) >= FAN_MIN:
            return fallback
    clipped = _clip_text(text, FAN_MAX)
    return clipped if len(clipped) >= FAN_MIN else None


def _fallback_fan_spotlight_object(facts: Dict[str, Any], language: str) -> Optional[Dict[str, str]]:
    """Generate fallback fan spotlight in new object format."""
    fan_team = facts.get("fan_team")
    if not fan_team:
        return None

    next_match = facts.get("next_match") or {}
    if not (next_match.get("home") and next_match.get("away")):
        return None

    opponent = next_match["away"] if next_match["home"] == fan_team else next_match["home"]
    kickoff = _format_paris_datetime(
        next_match.get("local_kickoff") or next_match.get("paris_kickoff") or next_match.get("utc_kickoff"),
        language,
    )
    
    # Get evolution data if available
    fan_evolution = facts.get("fan_evolution", {})
    current_pos = fan_evolution.get("current_stats", {}).get("position") if fan_evolution else None
    position_change = fan_evolution.get("change", 0) if fan_evolution else 0
    
    if language == "fr":
        analysis = f"{fan_team} occupe actuellement la {current_pos}e position" if current_pos else f"{fan_team}"
        if position_change > 0:
            analysis += f", en hausse de {position_change} place(s)."
        elif position_change < 0:
            analysis += f", en baisse de {abs(position_change)} place(s)."
        else:
            analysis += " maintient sa position."
        
        preview = f"Prochain match face à {opponent}"
        if kickoff:
            preview += f" ({kickoff})"
        preview += ". Un match crucial pour la suite de la saison."
        
        tactical = "Surveillez les transitions rapides et la pression haute. Le contrôle du milieu sera déterminant."
    else:
        analysis = f"{fan_team} currently sit in {current_pos}th position" if current_pos else f"{fan_team}"
        if position_change > 0:
            analysis += f", up {position_change} place(s)."
        elif position_change < 0:
            analysis += f", down {abs(position_change)} place(s)."
        else:
            analysis += " maintain their position."
        
        preview = f"Next up against {opponent}"
        if kickoff:
            preview += f" ({kickoff})"
        preview += ". A crucial match for the season ahead."
        
        tactical = "Watch for quick transitions and high pressing. Midfield control will be decisive."
    
    return {
        "analysis": analysis[:600],
        "next_match_preview": preview[:300],
        "tactical_notes": tactical[:250],
    }
