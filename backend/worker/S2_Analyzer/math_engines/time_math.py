from typing import List, Dict, Any
from backend.domain.process_data_models import NormalizedTicket

class TimeMath:
    """Math engine for time-based velocity and cycle calculations."""

    @staticmethod
    def sprint_item_timeline(tickets: List[NormalizedTicket]) -> List[Dict[str, Any]]:
        """Calculates exact days spent in each stage for Gantt charts."""
        SEC_TO_DAYS = 86400.0
        result = []
        for t in tickets:
            # Use human-readable title from comments field, fallback to ticket_id
            display_title = t.comments if t.comments else t.ticket_id
            # Try to extract a numeric issue number for display
            try:
                issue_num = int(t.ticket_id) if t.ticket_id.isdigit() else None
            except (ValueError, AttributeError):
                issue_num = None
            display_number = f"#{issue_num}" if issue_num else t.ticket_id
            
            result.append({
                "Sprint": t.sprint,
                "IssueNumber": display_number,
                "Title": display_title,
                "TodoDays": round(t.time_in_todo_sec / SEC_TO_DAYS, 2),
                "InProgressDays": round(t.time_in_progress_sec / SEC_TO_DAYS, 2),
                "InReviewDays": round(t.time_in_review_sec / SEC_TO_DAYS, 2),
                "TotalCycleDays": round((t.time_in_todo_sec + t.time_in_progress_sec + t.time_in_review_sec) / SEC_TO_DAYS, 2),
                "CurrentStatus": t.status_normalized,
                "Estimate": t.estimate,
                "IsBug": t.is_bug
            })
        return result

    @staticmethod
    def average_time_in_step(tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        """Averages the stage cycle times for the Sprint."""
        SEC_TO_DAYS = 86400.0
        total_items = len(tickets)
        bug_items = sum(1 for t in tickets if t.is_bug)
        avg_todo = sum(t.time_in_todo_sec for t in tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_in_progress = sum(t.time_in_progress_sec for t in tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_in_review = sum(t.time_in_review_sec for t in tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_cycle = avg_todo + avg_in_progress + avg_in_review

        return {
            "AvgTodoDays": round(avg_todo, 2),
            "AvgInProgressDays": round(avg_in_progress, 2),
            "AvgInReviewDays": round(avg_in_review, 2),
            "AvgCycleDays": round(avg_cycle, 2),
            "ItemCount": total_items,
            "BugItemCount": bug_items
        }
