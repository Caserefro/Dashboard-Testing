from typing import List, Dict, Any
from datetime import datetime
from backend.domain.process_data_models import NormalizedTicket, NormalizedPR

class QualityMath:
    """Math engine for quality, yield, and throughput calculations."""

    @staticmethod
    def first_time_yield(tickets: List[NormalizedTicket]) -> float:
        """
        FTY = (Completed Tickets with ZERO Reopen Loops / Total Completed Tickets) * 100.0
        Target: > 96%
        """
        completed = [t for t in tickets if t.status_normalized == "DONE"]
        if not completed:
            return 100.0

        clean_count = sum(1 for t in completed if t.is_first_time_yield)
        fty_raw = (clean_count / len(completed)) * 100.0
        return round(max(0.0, min(100.0, fty_raw)), 2)

    @staticmethod
    def pr_based_fty(prs: List[NormalizedPR]) -> Dict[str, Any]:
        """Calculates PR First Time Yield using Review Iteration math."""
        merged_prs = [p for p in prs if p.status_normalized == "MERGED"]
        total_merged = len(merged_prs)
        first_pass = sum(1 for p in merged_prs if p.review_cycles == 0)
        reworked = total_merged - first_pass
        fty_pct = round((first_pass / total_merged * 100.0) if total_merged > 0 else 100.0, 2)
        total_cycles = sum(p.review_cycles for p in merged_prs)
        avg_cycles = round((total_cycles / total_merged) if total_merged > 0 else 0.0, 2)
        avg_comments = round(sum(p.comment_count for p in merged_prs) / total_merged if total_merged > 0 else 0.0, 2)
        
        return {
            "TotalMergedPRs": total_merged,
            "FirstPassPRs": first_pass,
            "ReworkedPRs": reworked,
            "PRFTYPercentage": fty_pct,
            "AvgReviewCycles": avg_cycles,
            "AvgCommentsPerPR": avg_comments
        }

    @staticmethod
    def issue_loop_fty(tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        """Calculates Issue Loop FTY from the rework_loops property."""
        completed = [t for t in tickets if t.status_normalized == "DONE"]
        total_completed = len(completed)
        clean = sum(1 for t in completed if t.is_first_time_yield)
        reworked = total_completed - clean
        fty_pct = round((clean / total_completed * 100.0) if total_completed > 0 else 100.0, 2)
        total_loops = sum(t.rework_loops for t in completed)
        avg_loops_completed = round(total_loops / total_completed if total_completed > 0 else 0.0, 2)
        avg_loops_reworked = round(total_loops / reworked if reworked > 0 else 0.0, 2)

        return {
            "TotalCompletedItems": total_completed,
            "FirstTimeYieldItems": clean,
            "ReworkedItems": reworked,
            "FTYPercentage": fty_pct,
            "AvgReworkLoopsPerCompletedItem": avg_loops_completed,
            "AvgReworkLoopsPerReworkedItem": avg_loops_reworked
        }

    @staticmethod
    def sp_breakdown(tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        """Calculates Story Point ratio of Bug vs Non-Bug."""
        total_sp = sum(t.story_points for t in tickets)
        bug_sp = sum(t.story_points for t in tickets if t.is_bug)
        non_bug_sp = total_sp - bug_sp
        bug_pct = round((bug_sp / total_sp * 100.0) if total_sp > 0 else 0.0, 2)
        
        return {
            "TotalSP": total_sp,
            "BugSP": bug_sp,
            "BugPercentage": bug_pct,
            "NonBugSP": non_bug_sp
        }

    @staticmethod
    def tickets_per_day(tickets: List[NormalizedTicket]) -> List[Dict[str, Any]]:
        """Aggregates completed tickets grouped by weekday for the velocity bar chart widget."""
        day_counts: Dict[str, int] = {
            "Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0,
            "Friday": 0, "Saturday": 0, "Sunday": 0,
        }

        for t in tickets:
            if t.status_normalized == "DONE" and t.completed_date:
                try:
                    dt = datetime.strptime(t.completed_date[:10], "%Y-%m-%d")
                    day_name = dt.strftime("%A")
                    if day_name in day_counts:
                        day_counts[day_name] += 1
                except ValueError:
                    continue

        return [{"day_label": d, "tickets_merged": c} for d, c in day_counts.items()]
