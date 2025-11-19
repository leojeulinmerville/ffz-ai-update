"""
Service for comparing snapshots to identify changes and trends.
"""

from typing import Any, Dict, List, Optional

from app.services.analytics import (
    calculate_points_change,
    calculate_team_position_change,
)


def compare_snapshots(
    current: Dict[str, Any],
    previous: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare current snapshot with previous one to identify changes.
    
    Args:
        current: Current snapshot payload
        previous: Previous snapshot payload (from get_latest_snapshot_payload)
        
    Returns:
        Dict with:
        - position_changes: List of teams that moved positions
        - points_changes: List of teams with points changes
        - significant_movements: Teams that moved 3+ positions
        - table_evolution: Summary of table changes
    """
    if not previous:
        return {
            "position_changes": [],
            "points_changes": [],
            "significant_movements": [],
            "table_evolution": "no_previous_data",
        }
    
    current_table = current.get("table", [])
    previous_table = previous.get("table", [])
    
    if not current_table:
        return {
            "position_changes": [],
            "points_changes": [],
            "significant_movements": [],
            "table_evolution": "no_current_data",
        }
    
    position_changes: List[Dict[str, Any]] = []
    points_changes: List[Dict[str, Any]] = []
    significant_movements: List[Dict[str, Any]] = []
    
    # Analyze all teams in current table
    for team_row in current_table:
        team_name = team_row.get("team")
        if not team_name:
            continue
        
        # Check position change
        pos_change = calculate_team_position_change(
            current_table, previous_table, team_name
        )
        if pos_change and pos_change.get("change") != 0:
            position_changes.append(pos_change)
            # Significant movement: 3+ positions
            if abs(pos_change.get("change", 0)) >= 3:
                significant_movements.append(pos_change)
        
        # Check points change
        pts_change = calculate_points_change(
            current_table, previous_table, team_name
        )
        if pts_change and pts_change.get("change") != 0:
            points_changes.append(pts_change)
    
    # Sort by magnitude of change
    position_changes.sort(key=lambda x: abs(x.get("change", 0)), reverse=True)
    points_changes.sort(key=lambda x: abs(x.get("change", 0)), reverse=True)
    significant_movements.sort(key=lambda x: abs(x.get("change", 0)), reverse=True)
    
    return {
        "position_changes": position_changes[:10],  # Top 10 changes
        "points_changes": points_changes[:10],
        "significant_movements": significant_movements,
        "table_evolution": "analyzed",
    }


def get_team_evolution(
    current: Dict[str, Any],
    previous: Optional[Dict[str, Any]],
    team_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Get evolution data for a specific team.
    
    Args:
        current: Current snapshot
        previous: Previous snapshot
        team_name: Team to analyze
        
    Returns:
        Dict with position_change, points_change, and other metrics
    """
    if not current:
        return None
    
    current_table = current.get("table", [])
    previous_table = previous.get("table", []) if previous else None
    
    evolution: Dict[str, Any] = {
        "team": team_name,
    }
    
    # Position change
    pos_change = calculate_team_position_change(
        current_table, previous_table, team_name
    )
    if pos_change:
        evolution.update(pos_change)
    
    # Points change
    pts_change = calculate_points_change(
        current_table, previous_table, team_name
    )
    if pts_change:
        evolution["points"] = pts_change
    
    # Current stats
    for team in current_table:
        if (team.get("team") or "").lower() == team_name.lower():
            evolution["current_stats"] = {
                "position": team.get("rank"),
                "points": team.get("points"),
                "goals_for": team.get("goals_for"),
                "goals_against": team.get("goals_against"),
                "goal_difference": team.get("goals_for", 0) - team.get("goals_against", 0),
            }
            break
    
    return evolution if evolution.get("current_stats") else None

