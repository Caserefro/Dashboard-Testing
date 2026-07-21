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


def detect_sprint_window(work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scans all extracted items' Sprint fieldValues to auto-detect the current sprint window.
    Returns a dict with sprint_name, start_date, end_date, and total_ideal_points (sum of estimates).

    If multiple sprints exist, picks the one with the most items.
    """
    sprint_data: Dict[str, Dict[str, Any]] = {}

    for item in work_items:
        field_values = item.get("fieldValues", [])
        for fv in field_values:
            if fv.get("fieldName") == "Sprint" and fv.get("startDate"):
                sprint_name = fv.get("value", "Unknown Sprint")
                start_date = fv["startDate"]
                duration = int(fv.get("duration") or 14)

                if sprint_name not in sprint_data:
                    sprint_data[sprint_name] = {
                        "start_date": start_date,
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

    # Pick the sprint with the most items
    best_sprint_name = max(sprint_data, key=lambda k: sprint_data[k]["item_count"])
    best = sprint_data[best_sprint_name]

    try:
        start_dt = datetime.strptime(best["start_date"], "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=best["duration"])
        end_date_str = end_dt.strftime("%Y-%m-%d")
    except ValueError:
        end_date_str = best["start_date"]

    return {
        "sprint_name": best_sprint_name,
        "start_date": best["start_date"],
        "end_date": end_date_str,
        "total_ideal_points": best["total_sp"]
    }
