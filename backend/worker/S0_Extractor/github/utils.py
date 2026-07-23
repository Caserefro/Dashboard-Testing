"""
GitHub Extractor Utilities (`backend/worker/S0_Extractor/github/utils.py`)

Pure utility functions for post-processing raw GitHub GraphQL responses.
These are vendor-specific helpers that belong to the Extractor layer.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta


def filter_ghost_items(work_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Removes incomplete/ghost items from the extracted payload.
    Ghost items are Project V2 entries where the content is empty
    (e.g., PRs that weren't expanded, or deleted issues still linked to the project).
    """
    return [
        item for item in work_items
        if item.get("number") is not None and item.get("title") is not None
    ]


def detect_sprint_window(work_items: List[Dict[str, Any]], record_date: str = None) -> Dict[str, Any]:
    """
    Scans all extracted items' Sprint fieldValues to auto-detect the current active sprint window.
    Returns a dict with sprint_name, start_date, end_date, and total_ideal_points (sum of estimates).

    Prioritizes the sprint active on record_date (or today). If no active sprint covers today,
    picks the most recent completed/active sprint before picking future sprints.
    """
    if record_date is None:
        record_date = datetime.now().strftime("%Y-%m-%d")

    sprint_data: Dict[str, Dict[str, Any]] = {}

    for item in work_items:
        field_values = item.get("fieldValues", [])
        for fv in field_values:
            if fv.get("fieldName") == "Sprint" and fv.get("startDate"):
                sprint_name = fv.get("value", "Unknown Sprint")
                start_date = fv["startDate"]
                duration = int(fv.get("duration") or 14)

                if sprint_name not in sprint_data:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = start_dt + timedelta(days=duration)
                        end_date_str = end_dt.strftime("%Y-%m-%d")
                    except ValueError:
                        end_date_str = start_date

                    sprint_data[sprint_name] = {
                        "start_date": start_date,
                        "end_date": end_date_str,
                        "duration": duration,
                        "item_count": 0,
                        "total_sp": 0.0
                    }

                sprint_data[sprint_name]["item_count"] += 1

                # Sum story points for total_ideal_points
                for f in field_values:
                    if f.get("fieldName") == "Estimate":
                        try:
                            sprint_data[sprint_name]["total_sp"] += float(f.get("value") or 0)
                        except (ValueError, TypeError):
                            pass
                        break

    if not sprint_data:
        return {
            "sprint_name": None,
            "start_date": None,
            "end_date": None,
            "total_ideal_points": 0.0
        }

    # 1. Look for active sprint covering record_date
    active_sprints = [
        sname for sname, sinfo in sprint_data.items()
        if sinfo["start_date"] <= record_date <= sinfo["end_date"]
    ]

    if active_sprints:
        # If multiple overlap, pick the one with most items
        best_sprint_name = max(active_sprints, key=lambda k: sprint_data[k]["item_count"])
    else:
        # 2. Pick the sprint with start_date closest to record_date (avoiding distant future sprints)
        past_or_current = [
            sname for sname, sinfo in sprint_data.items()
            if sinfo["start_date"] <= record_date
        ]
        if past_or_current:
            best_sprint_name = max(past_or_current, key=lambda k: sprint_data[k]["start_date"])
        else:
            # Fallback to sprint with most items
            best_sprint_name = max(sprint_data, key=lambda k: sprint_data[k]["item_count"])

    best = sprint_data[best_sprint_name]

    return {
        "sprint_name": best_sprint_name,
        "start_date": best["start_date"],
        "end_date": best["end_date"],
        "total_ideal_points": best["total_sp"]
    }
