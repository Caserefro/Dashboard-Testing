from typing import Dict, Any
import csv
import io

class CsvFormatter:
    """Shapes computed KPIs into a clean CSV table string with all metric sections."""

    @staticmethod
    def format(computed_kpis: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        # --- Section 1: Summary Metrics ---
        writer.writerow(["Metric Summary", "Value"])
        writer.writerow(["First Time Yield (%)", computed_kpis.get("fty_percentage", 100.0)])
        
        sp = computed_kpis.get("sp_breakdown", {})
        writer.writerow(["Total Story Points", sp.get("TotalSP", 0)])
        writer.writerow(["Bug Story Points", sp.get("BugSP", 0)])
        writer.writerow(["Bug SP (%)", sp.get("BugPercentage", 0)])
        writer.writerow(["Non-Bug Story Points", sp.get("NonBugSP", 0)])
        writer.writerow([])

        # --- Section 2: Burndown Curve ---
        burndown_data = computed_kpis.get("burndown_curve", {})
        series_list = burndown_data if isinstance(burndown_data, list) else burndown_data.get("series", [])

        writer.writerow(["Burndown Curve"])
        writer.writerow(["Date", "Remaining Points", "Ideal Points", "Inverse Root Points"])
        for pt in series_list:
            writer.writerow([
                pt.get("date"),
                pt.get("remaining_points"),
                pt.get("ideal_points"),
                pt.get("inverse_root_points"),
            ])
        writer.writerow([])

        # --- Section 3: Tickets Per Day ---
        writer.writerow(["Tickets Per Day Chart"])
        writer.writerow(["Day Label", "Tickets Merged"])
        for row in computed_kpis.get("tickets_per_day_chart", []):
            writer.writerow([row.get("day_label"), row.get("tickets_merged")])
        writer.writerow([])

        # --- Section 4: Sprint Item Timeline (Gantt Data) ---
        writer.writerow(["Sprint Item Timeline"])
        writer.writerow(["Sprint", "IssueNumber", "Title", "TodoDays", "InProgressDays", "InReviewDays", "TotalCycleDays", "Status", "Estimate", "IsBug"])
        for item in computed_kpis.get("sprint_item_timeline", []):
            writer.writerow([
                item.get("Sprint"),
                item.get("IssueNumber"),
                item.get("Title"),
                item.get("TodoDays"),
                item.get("InProgressDays"),
                item.get("InReviewDays"),
                item.get("TotalCycleDays"),
                item.get("CurrentStatus"),
                item.get("Estimate"),
                item.get("IsBug"),
            ])
        writer.writerow([])

        # --- Section 5: Issue Loop FTY ---
        issue_fty = computed_kpis.get("issue_loop_fty", {})
        writer.writerow(["Issue Loop FTY"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Completed Items", issue_fty.get("TotalCompletedItems", 0)])
        writer.writerow(["First Time Yield Items", issue_fty.get("FirstTimeYieldItems", 0)])
        writer.writerow(["Reworked Items", issue_fty.get("ReworkedItems", 0)])
        writer.writerow(["FTY (%)", issue_fty.get("FTYPercentage", 100.0)])
        writer.writerow(["Avg Rework Loops (Completed)", issue_fty.get("AvgReworkLoopsPerCompletedItem", 0)])
        writer.writerow(["Avg Rework Loops (Reworked)", issue_fty.get("AvgReworkLoopsPerReworkedItem", 0)])
        writer.writerow([])

        # --- Section 6: PR-Based FTY ---
        pr_fty = computed_kpis.get("pr_based_fty", {})
        writer.writerow(["PR-Based FTY"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Merged PRs", pr_fty.get("TotalMergedPRs", 0)])
        writer.writerow(["First Pass PRs", pr_fty.get("FirstPassPRs", 0)])
        writer.writerow(["Reworked PRs", pr_fty.get("ReworkedPRs", 0)])
        writer.writerow(["PR FTY (%)", pr_fty.get("PRFTYPercentage", 100.0)])
        writer.writerow(["Avg Review Cycles", pr_fty.get("AvgReviewCycles", 0)])
        writer.writerow(["Avg Comments Per PR", pr_fty.get("AvgCommentsPerPR", 0)])
        writer.writerow([])

        # --- Section 7: Average Time in Step ---
        avg_time = computed_kpis.get("average_time_in_step", {})
        writer.writerow(["Average Time in Step"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Avg Todo Days", avg_time.get("AvgTodoDays", 0)])
        writer.writerow(["Avg In Progress Days", avg_time.get("AvgInProgressDays", 0)])
        writer.writerow(["Avg In Review Days", avg_time.get("AvgInReviewDays", 0)])
        writer.writerow(["Avg Cycle Days", avg_time.get("AvgCycleDays", 0)])
        writer.writerow(["Item Count", avg_time.get("ItemCount", 0)])
        writer.writerow(["Bug Item Count", avg_time.get("BugItemCount", 0)])

        return output.getvalue()
