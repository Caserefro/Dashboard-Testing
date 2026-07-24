from typing import List, Dict, Any
from datetime import datetime

try:
    from .extractor_config import STATUS_MAP
except ImportError:
    from backend.AnalyticsWorkerFactory.S0_Extractor.github.extractor_config import STATUS_MAP


def parse_iso_date(date_str: str) -> float:
    """Safely converts ISO-8601 string to epoch seconds."""
    try:
        # Handle 'Z' suffix
        clean_str = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0

def parse_issue_timeline(
    timeline_events: List[Dict[str, Any]], 
    created_at: str, 
    target_date_ts: float = None,
    sprint_start_date: str = None
) -> Dict[str, Any]:
    """
    Parses a GitHub ProjectV2ItemStatusChangedEvent timeline.
    Computes exact seconds spent in Todo, In Progress, Review, Dev Testing, and Rework.
    Calculates rework loops and supports clamping queue time to sprint_start_date.
    """
    time_in_todo = 0.0
    time_in_progress = 0.0
    time_in_review = 0.0
    time_in_dev_testing = 0.0
    time_in_rework = 0.0
    rework_loops = 0
    has_hit_review = False
    
    if target_date_ts is None:
        target_date_ts = datetime.now().timestamp()
        
    created_ts = parse_iso_date(created_at)
    
    # If ticket was created before the sprint started, clamp start to sprint_start_date
    if sprint_start_date:
        sprint_start_ts = parse_iso_date(sprint_start_date)
        if sprint_start_ts > 0 and created_ts < sprint_start_ts:
            created_ts = sprint_start_ts

    if created_ts > target_date_ts:
        # Ticket didn't even exist yet in our timeline window
        return {
            "time_in_todo_sec": 0.0,
            "time_in_progress_sec": 0.0,
            "time_in_review_sec": 0.0,
            "time_in_dev_testing_sec": 0.0,
            "time_in_rework_sec": 0.0,
            "rework_loops": 0
        }
        
    # Filter out events that haven't happened yet in our time-travel
    valid_events = []
    for ev in (timeline_events or []):
        ev_ts = parse_iso_date(ev.get("createdAt", ""))
        if ev_ts <= target_date_ts:
            valid_events.append(ev)

    if not valid_events:
        # It's stuck in Todo from creation (or sprint start) until target_date
        return {
            "time_in_todo_sec": max(0.0, target_date_ts - created_ts),
            "time_in_progress_sec": 0.0,
            "time_in_review_sec": 0.0,
            "time_in_dev_testing_sec": 0.0,
            "time_in_rework_sec": 0.0,
            "rework_loops": 0
        }

    # Sort events by time
    events = sorted(valid_events, key=lambda x: parse_iso_date(x.get("createdAt", "")))
    
    last_status = "Todo"
    last_ts = created_ts



    # Standardize statuses
    for ev in events:
        if ev.get("__typename") != "ProjectV2ItemStatusChangedEvent":
            continue
            
        current_ts = parse_iso_date(ev.get("createdAt", ""))
        delta = max(0.0, current_ts - last_ts)
        
        # Add time to the previous status
        norm_status = STATUS_MAP.get(last_status.lower(), "Todo")
        if norm_status == "Todo":
            if has_hit_review:
                time_in_rework += delta
            else:
                time_in_todo += delta
        elif norm_status == "InProgress":
            if has_hit_review:
                time_in_rework += delta
            else:
                time_in_progress += delta
        elif norm_status == "InReview":
            time_in_review += delta
        elif norm_status == "DevTesting":
            time_in_dev_testing += delta

        # Update last_status to the new status
        raw_status = ev.get("status", "") if isinstance(ev.get("status"), str) else (ev.get("status", {}).get("name", "") if isinstance(ev.get("status"), dict) else "")
        new_norm_status = STATUS_MAP.get(raw_status.lower(), "Todo")
        
        # Check for backwards movement (rework)
        if norm_status in ["InReview", "DevTesting", "Done"] and new_norm_status in ["Todo", "InProgress"]:
            rework_loops += 1
            
        if new_norm_status in ["InReview", "DevTesting"]:
            has_hit_review = True
            
        last_status = raw_status
        last_ts = current_ts

    # If the ticket is currently active, we add the time from the last event until the target_date
    final_delta = max(0.0, target_date_ts - last_ts)
    final_norm = STATUS_MAP.get(last_status.lower(), "Todo")
    if final_norm == "Todo":
        if has_hit_review:
            time_in_rework += final_delta
        else:
            time_in_todo += final_delta
    elif final_norm == "InProgress":
        if has_hit_review:
            time_in_rework += final_delta
        else:
            time_in_progress += final_delta
    elif final_norm == "InReview":
        time_in_review += final_delta
    elif final_norm == "DevTesting":
        time_in_dev_testing += final_delta

    return {
        "time_in_todo_sec": time_in_todo,
        "time_in_progress_sec": time_in_progress,
        "time_in_review_sec": time_in_review,
        "time_in_dev_testing_sec": time_in_dev_testing,
        "time_in_rework_sec": time_in_rework,
        "rework_loops": rework_loops,
        "current_status": final_norm
    }

def parse_pr_timeline(timeline_events: List[Dict[str, Any]]) -> int:
    """Counts how many ReviewRequested events occurred (review cycles)."""
    cycles = 0
    for ev in timeline_events:
        if ev.get("__typename") == "ReviewRequestedEvent":
            cycles += 1
    return cycles
