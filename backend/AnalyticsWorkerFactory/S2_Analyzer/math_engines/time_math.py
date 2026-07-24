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
            ct = (t.time_in_progress_sec + t.time_in_review_sec + getattr(t, "time_in_dev_testing_sec", 0.0) + t.time_in_rework_sec) / SEC_TO_DAYS
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
                "DevTestingDays": round(getattr(t, "time_in_dev_testing_sec", 0.0) / SEC_TO_DAYS, 2),
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
        avg_dev_testing = sum(getattr(t, "time_in_dev_testing_sec", 0.0) for t in valid_tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        avg_rework = sum(t.time_in_rework_sec for t in valid_tickets) / SEC_TO_DAYS / total_items if total_items > 0 else 0.0
        # Active Engineering Cycle Time = In Progress + In Review + Dev Testing + Rework
        avg_active_cycle = avg_in_progress + avg_in_review + avg_dev_testing + avg_rework

        return {
            "AvgTodoDays": round(avg_todo, 2),
            "AvgInProgressDays": round(avg_in_progress, 2),
            "AvgInReviewDays": round(avg_in_review, 2),
            "AvgDevTestingDays": round(avg_dev_testing, 2),
            "AvgReworkDays": round(avg_rework, 2),
            "AvgCycleDays": round(avg_active_cycle, 2),
            "ItemCount": total_items,
            "BugItemCount": bug_items,
            "OutliersExcluded": len(tickets) - total_items
        }

    @staticmethod
    def average_time_by_estimate(tickets: List[NormalizedTicket]) -> Dict[str, Dict[str, float]]:
        """Calculates average stage time for estimates in RAW or BUCKETED mode from board_config."""
        SEC_TO_DAYS = 86400.0
        cycle_times, upper_bound = TimeMath._get_cycle_times_and_bound(tickets)
        
        try:
            from backend.AnalyticsWorkerFactory.S2_Analyzer.analyzer_config import ESTIMATE_BUCKET_CONFIG
        except ImportError:
            ESTIMATE_BUCKET_CONFIG = {"MODE": "RAW"}

        valid_tickets = []
        for i, t in enumerate(tickets):
            if cycle_times[i] <= upper_bound:
                valid_tickets.append(t)

        mode = ESTIMATE_BUCKET_CONFIG.get("MODE", "RAW")
        buckets: Dict[str, List[NormalizedTicket]] = {}

        if mode == "RAW":
            # Group by exact numeric estimate value (e.g. E1, E2, E3, E4, E5, E6...)
            for t in valid_tickets:
                est = float(t.estimate) if t.estimate is not None else 0.0
                est_key = f"E{int(est)}" if est.is_integer() else f"E{est}"
                if est_key not in buckets:
                    buckets[est_key] = []
                buckets[est_key].append(t)
            
            # Sort keys numerically (E1, E2, E3, E4, E5, E6...)
            sorted_keys = sorted(buckets.keys(), key=lambda k: float(k[1:]) if k[1:].replace('.', '', 1).isdigit() else 0.0)
            sorted_buckets = {k: buckets[k] for k in sorted_keys}
            buckets = sorted_buckets
        else:
            # Bucketed mode using defined ranges
            ranges = ESTIMATE_BUCKET_CONFIG.get("RANGES", {"E2": (0.0, 3.0), "E4": (3.0, 6.0), "E8": (6.0, 12.0), "E16": (12.0, 999.0)})
            for key in ranges:
                buckets[key] = []
            for t in valid_tickets:
                est = float(t.estimate) if t.estimate is not None else 0.0
                matched = False
                for bkey, (low, high) in ranges.items():
                    if low < est <= high or (low == 0.0 and est <= high):
                        buckets[bkey].append(t)
                        matched = True
                        break
                if not matched and ranges:
                    last_key = list(ranges.keys())[-1]
                    buckets[last_key].append(t)

        result: Dict[str, Dict[str, float]] = {}
        for bucket_key, group_tix in buckets.items():
            count = len(group_tix)
            if count == 0:
                result[bucket_key] = {"todo": 0.0, "in_progress": 0.0, "in_review": 0.0, "dev_testing": 0.0, "merged": 0.0}
                continue
                
            avg_todo = sum(t.time_in_todo_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_in_progress = sum(t.time_in_progress_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_in_review = sum(t.time_in_review_sec for t in group_tix) / SEC_TO_DAYS / count
            avg_dev_testing = sum(getattr(t, "time_in_dev_testing_sec", 0.0) for t in group_tix) / SEC_TO_DAYS / count
            avg_rework = sum(t.time_in_rework_sec for t in group_tix) / SEC_TO_DAYS / count
            
            # Active Engineering Effort = In Progress + In Review + Dev Testing + Rework
            avg_active_cycle = avg_in_progress + avg_in_review + avg_dev_testing + avg_rework
            
            result[bucket_key] = {
                "todo": round(avg_todo, 2),
                "in_progress": round(avg_in_progress, 2),
                "in_review": round(avg_in_review, 2),
                "dev_testing": round(avg_dev_testing, 2),
                "merged": round(avg_active_cycle, 2)
            }
            
        return result
