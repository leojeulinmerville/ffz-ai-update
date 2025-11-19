"""
Analytics engine for calculating football statistics and trends.
Provides enriched data for LLM generation.
"""

from typing import Any, Dict, List, Optional, Tuple


def calculate_team_form(
    team_name: str,
    fixtures: List[Dict[str, Any]],
    results: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """
    Calculate recent form for a team (W/D/L).
    
    Args:
        team_name: Name of the team
        fixtures: List of fixtures with home/away teams
        results: Optional list of results with scores
        
    Returns:
        List of form indicators: ['W', 'D', 'L', 'W', 'D'] for last 5 matches
    """
    if not fixtures:
        return []
    
    # For now, we can't calculate actual form without results
    # This is a placeholder that will be enhanced when we have match results
    form: List[str] = []
    
    # If we had results, we would calculate:
    # for result in results[-5:]:
    #     if result['home'] == team_name:
    #         if result['home_score'] > result['away_score']:
    #             form.append('W')
    #         elif result['home_score'] == result['away_score']:
    #             form.append('D')
    #         else:
    #             form.append('L')
    #     elif result['away'] == team_name:
    #         if result['away_score'] > result['home_score']:
    #             form.append('W')
    #         elif result['away_score'] == result['home_score']:
    #             form.append('D')
    #         else:
    #             form.append('L')
    
    return form[:5]  # Return last 5 matches


def calculate_statistics(table_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate league-wide statistics.
    
    Args:
        table_data: List of team standings with goals_for, goals_against, points
        
    Returns:
        Dict with:
        - best_attack: Team with most goals_for
        - best_defense: Team with fewest goals_against
        - best_form: Team with most points in recent matches (if available)
        - struggling: Team with fewest points (bottom of table)
    """
    if not table_data:
        return {}
    
    stats: Dict[str, Any] = {}
    
    # Best attack (most goals scored)
    best_attack_team = max(
        table_data,
        key=lambda x: x.get("goals_for", 0),
        default=None
    )
    if best_attack_team:
        stats["best_attack"] = {
            "team": best_attack_team.get("team"),
            "goals": best_attack_team.get("goals_for", 0),
        }
    
    # Best defense (fewest goals conceded)
    best_defense_team = min(
        table_data,
        key=lambda x: x.get("goals_against", 999),
        default=None
    )
    if best_defense_team and best_defense_team.get("goals_against") is not None:
        stats["best_defense"] = {
            "team": best_defense_team.get("team"),
            "goals_against": best_defense_team.get("goals_against", 0),
        }
    
    # Team in form (most points - simplified, would need form data for accuracy)
    if table_data:
        top_team = table_data[0] if table_data else None
        if top_team:
            stats["best_form"] = {
                "team": top_team.get("team"),
                "points": top_team.get("points", 0),
            }
        
        # Struggling team (bottom of table)
        bottom_team = table_data[-1] if len(table_data) > 0 else None
        if bottom_team:
            stats["struggling"] = {
                "team": bottom_team.get("team"),
                "points": bottom_team.get("points", 0),
                "position": bottom_team.get("rank", len(table_data)),
            }
    
    return stats


def identify_trends(table_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify interesting trends in the league table.
    
    Args:
        table_data: Current league standings
        
    Returns:
        Dict with trends:
        - tight_race: Teams close in points at the top
        - relegation_battle: Teams close in points at the bottom
        - mid_table_cluster: Teams bunched in middle
    """
    if not table_data or len(table_data) < 3:
        return {}
    
    trends: Dict[str, Any] = {}
    
    # Tight race at the top (top 3 within 3 points)
    top_3 = table_data[:3]
    if len(top_3) >= 2:
        top_points = [t.get("points", 0) for t in top_3]
        if max(top_points) - min(top_points) <= 3:
            trends["tight_race"] = {
                "teams": [t.get("team") for t in top_3],
                "point_range": f"{min(top_points)}-{max(top_points)}",
            }
    
    # Relegation battle (bottom 3 within 3 points)
    if len(table_data) >= 3:
        bottom_3 = table_data[-3:]
        bottom_points = [t.get("points", 0) for t in bottom_3]
        if max(bottom_points) - min(bottom_points) <= 3:
            trends["relegation_battle"] = {
                "teams": [t.get("team") for t in bottom_3],
                "point_range": f"{min(bottom_points)}-{max(bottom_points)}",
            }
    
    return trends


def calculate_team_position_change(
    current_table: List[Dict[str, Any]],
    previous_table: Optional[List[Dict[str, Any]]],
    team_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Calculate position change for a specific team.
    
    Args:
        current_table: Current league standings
        previous_table: Previous league standings (from snapshot)
        team_name: Name of the team to check
        
    Returns:
        Dict with:
        - current_position: Current rank
        - previous_position: Previous rank (if available)
        - change: +N (up), -N (down), or 0 (same)
        - trend: "up", "down", or "stable"
    """
    if not current_table:
        return None
    
    # Find current position
    current_pos = None
    for idx, team in enumerate(current_table, start=1):
        if (team.get("team") or "").lower() == team_name.lower():
            current_pos = team.get("rank", idx)
            break
    
    if current_pos is None:
        return None
    
    result: Dict[str, Any] = {
        "current_position": current_pos,
        "team": team_name,
    }
    
    if previous_table:
        # Find previous position
        previous_pos = None
        for idx, team in enumerate(previous_table, start=1):
            if (team.get("team") or "").lower() == team_name.lower():
                previous_pos = team.get("rank", idx)
                break
        
        if previous_pos is not None:
            change = previous_pos - current_pos  # Positive = moved up
            result["previous_position"] = previous_pos
            result["change"] = change
            result["trend"] = "up" if change > 0 else "down" if change < 0 else "stable"
        else:
            result["trend"] = "new"
    else:
        result["trend"] = "unknown"
    
    return result


def calculate_points_change(
    current_table: List[Dict[str, Any]],
    previous_table: Optional[List[Dict[str, Any]]],
    team_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Calculate points change for a specific team.
    
    Args:
        current_table: Current league standings
        previous_table: Previous league standings
        team_name: Name of the team
        
    Returns:
        Dict with current_points, previous_points, change
    """
    if not current_table:
        return None
    
    # Find current points
    current_team = None
    for team in current_table:
        if (team.get("team") or "").lower() == team_name.lower():
            current_team = team
            break
    
    if not current_team:
        return None
    
    current_points = current_team.get("points", 0)
    result: Dict[str, Any] = {
        "current_points": current_points,
        "team": team_name,
    }
    
    if previous_table:
        previous_team = None
        for team in previous_table:
            if (team.get("team") or "").lower() == team_name.lower():
                previous_team = team
                break
        
        if previous_team:
            previous_points = previous_team.get("points", 0)
            change = current_points - previous_points
            result["previous_points"] = previous_points
            result["change"] = change
            result["trend"] = "gain" if change > 0 else "loss" if change < 0 else "stable"
    
    return result

