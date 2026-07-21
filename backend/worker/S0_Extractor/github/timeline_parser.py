from typing import List, Dict, Any
from datetime import datetime

def parse_iso_date(date_str: str) -> float:
    """Safely converts ISO-8601 string to epoch seconds."""
    try:
        # Handle 'Z' suffix
        clean_str = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0

def parse_issue_timeline(timeline_events: List[Dict[str, Any]], created_at: str) -> Dict[str, Any]:
    """
    Parses a GitHub ProjectV2ItemStatusChangedEvent timeline.
    Computes exact seconds spent in Todo, In Progress, and Review.
    Also calculates rework loops (how many times it moved backward).
    """
    time_in_todo = 0.0
    time_in_progress = 0.0
    time_in_review = 0.0
    rework_loops = 0
    
    if not timeline_events:
        return {
            "time_in_todo_sec": 0.0,
            "time_in_progress_sec": 0.0,
            "time_in_review_sec": 0.0,
            "rework_loops": 0
        }

    # Sort events by time
    events = sorted(timeline_events, key=lambda x: parse_iso_date(x.get("createdAt", "")))
    
    last_status = "Todo"
    last_ts = parse_iso_date(created_at)

    STATUS_MAP = {
        "todo": "Todo",
        "to do": "Todo",
        "in progress": "InProgress",
        "doing": "InProgress",
        "in review": "InReview",
        "review": "InReview",
        "done": "Done",
        "closed": "Done"
    }

    # Standardize statuses
    for ev in events:
        if ev.get("__typename") != "ProjectV2ItemStatusChangedEvent":
            continue
            
        current_ts = parse_iso_date(ev.get("createdAt", ""))
        delta = current_ts - last_ts
        
        # Add time to the previous status
        norm_status = STATUS_MAP.get(last_status.lower(), "Todo")
        if norm_status == "Todo":
            time_in_todo += delta
        elif norm_status == "InProgress":
            time_in_progress += delta
        elif norm_status == "InReview":
            time_in_review += delta

        # Update last_status to the new status
        raw_status = ev.get("status", {}).get("name", "") if ev.get("status") else ""
        new_norm_status = STATUS_MAP.get(raw_status.lower(), "Todo")
        
        # Check for backwards movement (rework)
        if norm_status in ["InReview", "Done"] and new_norm_status in ["Todo", "InProgress"]:
            rework_loops += 1
            
        last_status = raw_status
        last_ts = current_ts

    # If the ticket is currently active, we add the time from the last event until NOW
    now_ts = datetime.now().timestamp()
    final_delta = now_ts - last_ts
    final_norm = STATUS_MAP.get(last_status.lower(), "Todo")
    if final_norm == "Todo":
        time_in_todo += final_delta
    elif final_norm == "InProgress":
        time_in_progress += final_delta
    elif final_norm == "InReview":
        time_in_review += final_delta

    return {
        "time_in_todo_sec": time_in_todo,
        "time_in_progress_sec": time_in_progress,
        "time_in_review_sec": time_in_review,
        "rework_loops": rework_loops
    }

def parse_pr_timeline(timeline_events: List[Dict[str, Any]]) -> int:
    """Counts how many ReviewRequested events occurred (review cycles)."""
    cycles = 0
    for ev in timeline_events:
        if ev.get("__typename") == "ReviewRequestedEvent":
            cycles += 1
    return cycles
