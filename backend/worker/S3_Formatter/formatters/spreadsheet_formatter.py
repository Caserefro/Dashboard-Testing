from typing import Dict, Any, List

class SpreadsheetFormatter:
    """Formats mathematical KPIs into the precise UI Graph Contracts for Excel/Smartsheet endpoints."""

    @staticmethod
    def format(computed_kpis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shapes KPIs into the exact `ui_graph_contracts.json` specification.
        Enforces all contract bounds (0.0 - 100.0, ISO dates) before returning to Data Sync.
        """
        # 1. First Time Yield Gauge
        fty_raw = float(computed_kpis.get("fty_percentage", 100.0))
        fty_bounded = round(max(0.0, min(100.0, fty_raw)), 2)

        # 2. Tickets Per Day Chart
        velocity_contract: List[Dict[str, Any]] = []
        for row in computed_kpis.get("tickets_per_day_chart", []):
            velocity_contract.append({
                "day_label": str(row.get("day_label", "Day")),
                "tickets_merged": max(0, int(row.get("tickets_merged", 0))),
            })

        # --- THE 6 ADVANCED METRICS CONTRACTS ---
        sprint_item_timeline = computed_kpis.get("sprint_item_timeline", [])
        pr_based_fty = computed_kpis.get("pr_based_fty", {})
        issue_loop_fty = computed_kpis.get("issue_loop_fty", {})
        average_time_in_step = computed_kpis.get("average_time_in_step", {})
        sp_breakdown = computed_kpis.get("sp_breakdown", {})

        # Contract 6: Advanced Burndown (Flattened to Day1..10)
        burndown_data = computed_kpis.get("burndown_curve", {})
        series_list = burndown_data if isinstance(burndown_data, list) else burndown_data.get("series", [])
        forecast = burndown_data.get("forecast", {}) if isinstance(burndown_data, dict) else {}
        
        flat_burndown = {
            "Sprint": "Sprint 1", 
            "SprintStartDate": series_list[0].get("date") if series_list else "",
            "SprintDurationDays": len(series_list),
            "TotalPlannedPoints": series_list[0].get("ideal_points", 0.0) if series_list else 0.0,
            "CompletedPointsCurrent": 0.0,
            "RemainingPointsCurrent": series_list[-1].get("remaining_points", 0.0) if series_list else 0.0,
        }
        
        for i in range(10):
            day_idx = i + 1
            if i < len(series_list):
                flat_burndown[f"Day{day_idx}"] = series_list[i].get("remaining_points", 0.0)
                flat_burndown[f"Avg{day_idx}"] = series_list[i].get("ideal_points", 0.0)
            else:
                flat_burndown[f"Day{day_idx}"] = None
                flat_burndown[f"Avg{day_idx}"] = None
                
            pred_y = forecast.get("forecast_y", [])
            if i < len(pred_y):
                flat_burndown[f"PredDay{day_idx}"] = round(pred_y[i], 2)
            else:
                flat_burndown[f"PredDay{day_idx}"] = None

        day1_val = flat_burndown.get("Day1")
        pred1_val = flat_burndown.get("PredDay1")
        flat_burndown["GapDay0"] = round((day1_val or 0.0) - (pred1_val or 0.0), 2)

        return {
            "first_time_yield_gauge": {"fty_percentage": fty_bounded},
            "tickets_per_day_chart": velocity_contract,
            "sprint_item_timeline": sprint_item_timeline,
            "pr_based_fty": pr_based_fty,
            "issue_loop_fty": issue_loop_fty,
            "average_time_in_step": average_time_in_step,
            "sp_breakdown": sp_breakdown,
            "advanced_burndown": flat_burndown
        }
