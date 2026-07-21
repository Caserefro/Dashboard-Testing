from typing import Dict, Any
import csv
import io

class CsvFormatter:
    """Shapes computed KPIs into a clean CSV table string."""

    @staticmethod
    def format(computed_kpis: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Metric Summary", "Value"])
        writer.writerow(["First Time Yield (%)", computed_kpis.get("fty_percentage", 100.0)])
        writer.writerow([])
        
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

        writer.writerow(["Tickets Per Day Chart"])
        writer.writerow(["Day Label", "Tickets Merged"])
        for row in computed_kpis.get("tickets_per_day_chart", []):
            writer.writerow([row.get("day_label"), row.get("tickets_merged")])

        return output.getvalue()
