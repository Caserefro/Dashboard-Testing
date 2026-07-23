from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from backend.domain.process_data_models import NormalizedTicket

class TimeMath:
    """Math engine for time-based velocity and cycle calculations."""
    
    @staticmethod
    def _get_cycle_times_and_bound(tickets: List[NormalizedTicket]) -> Tuple[List[float], float]:
        """Calculates total cycle times and the 1.5x IQR upper bound for outliers."""
        SEC_TO_DAYS = 86400.0
        cycle_times = []
        for t in tickets:
            ct = (t.time_in_todo_sec + t.time_in_progress_sec + t.time_in_review_sec + t.time_in_rework_sec) / SEC_TO_DAYS
            cycle_times.append(ct)
            
        if not cycle_times or len(cycle_times) < 4:
            # Not enough data for meaningful IQR, return a massive bound
            return cycle_times, float('inf')
            
        q1 = np.percentile(cycle_times, 25)
        q3 = np.percentile(cycle_times, 75)
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr
        
        # If IQR is exactly 0 (e.g. all 0s), allow anything that is 0
        if upper_bound == 0:
            upper_bound = 0.0001
            
        return cycle_times, upper_bound

    @staticmethod
    def sprint_item_timeline(tickets: List[NormalizedTicket], target_sprint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Calculates exact days spent in each stage for Gantt charts, filtered strictly to target_sprint items."""
        SEC_TO_DAYS = 86400.0
        
        # Filter tickets to target_sprint if specified
        if target_sprint:
            filtered = [t for t in tickets if t.sprint == target_sprint]
            if filtered:
                tickets = filtered
        else:
            # Fallback: Auto-detect primary non-null sprint among tickets
            sprint_counts: Dict[str, int] = {}
            for t in tickets:
                if t.sprint:
                    sprint_counts[t.sprint] = sprint_counts.get(t.sprint, 0) + 1
            if sprint_counts:
                primary_sprint = max(sprint_counts, key=sprint_counts.get)
                filtered = [t for t in tickets if t.sprint == primary_sprint]
                if filtered:
                    tickets = filtered

        cycle_times, upper_bound = TimeMath._get_cycle_times_and_bound(tickets)
        
        result = []
        for i, t in enumerate(tickets):
            # Use human-readable title
            display_title = t.title if t.title else t.ticket_id
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
                "ReworkDays": round(t.time_in_rework_sec / SEC_TO_DAYS, 2),
                "TotalCycleDays": round(cycle_times[i], 2),
                "CurrentStatus": t.status_normalized,
                "Estimate": t.estimate,
                "IsBug": t.is_bug
            })
        return result

    @staticmethod
    def average_time_in_step(tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        """Averages the stage cycle times for the Sprint, excluding outliers."""
        SEC_TO_DAYS = 86400.0
        cycle_times, upper_bound = TimeMath._get_cycle_times_and_bound(tickets)
        
        valid_tickets = []
        for i, t in enumerate(tickets):
            if cycle_times[i] <= upper_bound:
                valid_tickets.append(t)
                
        total_items = len(valid_tickets)
        bug_items = sum(1 for t in valid_tickets if t.is_bug)
        
        avg_todo = sum(t.time_in_todo_sec for t in valid_tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_in_progress = sum(t.time_in_progress_sec for t in valid_tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_in_review = sum(t.time_in_review_sec for t in valid_tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_rework = sum(t.time_in_rework_sec for t in valid_tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_cycle = avg_todo + avg_in_progress + avg_in_review + avg_rework

        return {
            "AvgTodoDays": round(avg_todo, 2),
            "AvgInProgressDays": round(avg_in_progress, 2),
            "AvgInReviewDays": round(avg_in_review, 2),
            "AvgReworkDays": round(avg_rework, 2),
            "AvgCycleDays": round(avg_cycle, 2),
            "ItemCount": total_items,
            "BugItemCount": bug_items,
            "OutliersExcluded": len(tickets) - total_items
        }

    @staticmethod
    def average_time_by_estimate(tickets: List[NormalizedTicket]) -> Dict[str, Dict[str, float]]:
        """Calculates the average stage time grouped by ticket estimate (e.g., E2, E4, E8, E16)."""
        SEC_TO_DAYS = 86400.0
        cycle_times, upper_bound = TimeMath._get_cycle_times_and_bound(tickets)
        
        valid_tickets = []
        for i, t in enumerate(tickets):
            if cycle_times[i] <= upper_bound:
                valid_tickets.append(t)

        groups: Dict[float, List[NormalizedTicket]] = {}
        for t in valid_tickets:
            # We group by the float value of the estimate, defaulting to 0.0 if not found
            est = float(t.estimate) if t.estimate is not None else 0.0
            if est not in groups:
                groups[est] = []
            groups[est].append(t)

        result: Dict[str, Dict[str, float]] = {}
        for est, group_tix in groups.items():
            count = len(group_tix)
            if count == 0:
                continue
                
            avg_todo = sum(t.time_in_todo_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_in_progress = sum(t.time_in_progress_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_in_review = sum(t.time_in_review_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_rework = sum(t.time_in_rework_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_cycle = avg_todo + avg_in_progress + avg_in_review + avg_rework
            
            # Format as E2, E4, E8 etc. if it is a whole number, else E2.5
            est_key = f"E{int(est)}" if est.is_integer() else f"E{est}"
            result[est_key] = {
                "todo": round(avg_todo, 2),
                "in_progress": round(avg_in_progress, 2),
                "in_review": round(avg_in_review, 2),
                "merged": round(avg_cycle, 2)  # Treating 'merged' column in CSV as total cycle/merged time
            }
            
        return result
