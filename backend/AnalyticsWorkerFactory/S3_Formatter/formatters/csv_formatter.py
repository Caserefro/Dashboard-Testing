from typing import Dict, Any
import csv
import io
from itertools import zip_longest

class CsvFormatter:
    """Shapes computed KPIs into a clean CSV table string with all metric sections."""

    @staticmethod
    def format(computed_kpis: Dict[str, Any]) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(output)

        # --- Extrapolate Required Metrics ---
        timeline = computed_kpis.get("sprint_item_timeline", [])
        
        # Sprint state aggregations
        issues_total = len(timeline)
        issues_todo = sum(1 for t in timeline if t.get("CurrentStatus") == "TODO")
        issues_in_progress = sum(1 for t in timeline if t.get("CurrentStatus") == "IN_PROGRESS")
        issues_in_review = sum(1 for t in timeline if t.get("CurrentStatus") == "IN_REVIEW")
        issues_merged = sum(1 for t in timeline if t.get("CurrentStatus") == "DONE")
        
        # Story Points
        sp = computed_kpis.get("sp_breakdown", {})
        sp_total = sp.get("TotalSP", 0.0)
        sp_bug = sp.get("BugSP", 0.0)
        sp_non_bug = sp.get("NonBugSP", 0.0)
        sp_clean_pct = sp.get("NonBugPercentage", 100.0)
        
        # Quality
        issue_fty = computed_kpis.get("issue_loop_fty", {})
        reentries = issue_fty.get("AvgReworkLoopsPerCompletedItem", 0.0)

        # --- Build Left Side (Daily Aggregation & Burndown) ---
        burndown_data = computed_kpis.get("burndown_curve", {})
        series_list = burndown_data if isinstance(burndown_data, list) else burndown_data.get("series", [])
        avg_est = computed_kpis.get("average_time_by_estimate", {})

        est_keys = ["E2", "E4", "E8", "E16"]
        
        left_headers = [
            "record_date", "Sprint", "issues_total", "issues_todo", "issues_in_progress", "issues_in_review", "issues_merged",
            "avg_time_todo_E2", "avg_time_in_progress_E2", "avg_time_in_review_E2", "avg_time_merged_E2",
            "avg_time_todo_E4", "avg_time_in_progress_E4", "avg_time_in_review_E4", "avg_time_merged_E4",
            "avg_time_todo_E8", "avg_time_in_progress_E8", "avg_time_in_review_E8", "avg_time_merged_E8",
            "avg_time_todo_E16", "avg_time_in_progress_E16", "avg_time_in_review_E16", "avg_time_merged_E16",
            "story_points_total", "story_points_bug", "story_points_non_bug", "story_points_clean_pct",
            "average_prs_per_issue", "reentries_per_issue",
            "BurndownSP", "BurndownAVGSP", "BurndownPredictionSP", "SPDelta"
        ]
        
        from backend.application.sprint_service import ExcelSprintCalendarService, SprintInfo
        excel_service = ExcelSprintCalendarService()

        left_rows = []
        for pt in series_list:
            raw_date = pt.get("date", "")
            raw_sprint = timeline[0].get("Sprint", "") if timeline else ""
            
            # Format Column 1 & 2 via ExcelSprintCalendarService
            sinfo = SprintInfo(title=raw_sprint or "Sprint 1", start_date=raw_date, end_date=raw_date, duration=0)
            cal_rows = excel_service.generate_excel_calendar_rows(sinfo)
            date, sprint_name = cal_rows[0] if cal_rows else (raw_date, raw_sprint)
            
            b_rem = pt.get("remaining_points", 0.0)
            b_idl = pt.get("baseline_points", pt.get("ideal_points", 0.0))
            b_pred = pt.get("prediction_points", 0.0)
            sp_delta = round(b_rem - b_idl, 2)
            
            e2 = avg_est.get("E2", {})
            e4 = avg_est.get("E4", {})
            e8 = avg_est.get("E8", {})
            e16 = avg_est.get("E16", {})
            
            row = [
                date, sprint_name, issues_total, issues_todo, issues_in_progress, issues_in_review, issues_merged,
                e2.get("todo", 0.0), e2.get("in_progress", 0.0), e2.get("in_review", 0.0), e2.get("merged", 0.0),
                e4.get("todo", 0.0), e4.get("in_progress", 0.0), e4.get("in_review", 0.0), e4.get("merged", 0.0),
                e8.get("todo", 0.0), e8.get("in_progress", 0.0), e8.get("in_review", 0.0), e8.get("merged", 0.0),
                e16.get("todo", 0.0), e16.get("in_progress", 0.0), e16.get("in_review", 0.0), e16.get("merged", 0.0),
                sp_total, sp_bug, sp_non_bug, sp_clean_pct,
                computed_kpis.get("average_prs_per_issue", 0.0), reentries,
                b_rem, b_idl, b_pred, sp_delta
            ]
            left_rows.append(row)
            
        # --- Build Right Side (Sprint Timeline) ---
        right_headers = ["Title", "Sprint", "TodoDays", "InProgressDays", "InReviewDays", "DevTestingDays", "ReworkDays"]
        right_rows = []
        for item in timeline:
            right_rows.append([
                item.get("Title"),
                item.get("Sprint"),
                item.get("TodoDays"),
                item.get("InProgressDays"),
                item.get("InReviewDays"),
                item.get("DevTestingDays", 0.0),
                item.get("ReworkDays", 0.0)
            ])
            
        # Write headers with a double empty column separator
        writer.writerow(left_headers + ["", ""] + right_headers)
        
        # Zip them together
        for left, right in zip_longest(left_rows, right_rows, fillvalue=[]):
            # Pad left with empty strings if it ran out
            left_padded = left if left else [""] * len(left_headers)
            # Pad right with empty strings if it ran out
            right_padded = right if right else [""] * len(right_headers)
            
            writer.writerow(left_padded + ["", ""] + right_padded)

        return output.getvalue()
