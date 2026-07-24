from typing import Dict, Any

class HtmlFormatter:
    """Shapes computed KPIs into a clean HTML summary card."""

    @staticmethod
    def format(computed_kpis: Dict[str, Any]) -> str:
        fty = computed_kpis.get("fty_percentage", 100.0)
        html = [
            "<div style='font-family: Arial, sans-serif; padding: 16px; border: 1px solid #ccc; border-radius: 8px;'>",
            f"<h2 style='color: #1565c0;'>Project ATLAS - Worker Report</h2>",
            f"<p><strong>First Time Yield (FTY):</strong> <span style='color: #2e7d32; font-size: 1.2em;'>{fty}%</span></p>",
            "<h3>Burndown Daily Series</h3>",
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>",
            "<tr style='background-color: #f5f5f5;'><th>Date</th><th>Remaining</th><th>Ideal</th></tr>",
        ]
        
        burndown_data = computed_kpis.get("burndown_curve", {})
        series_list = burndown_data if isinstance(burndown_data, list) else burndown_data.get("series", [])
        
        for pt in series_list:
            html.append(
                f"<tr><td>{pt.get('date')}</td><td>{pt.get('remaining_points')}</td><td>{pt.get('ideal_points')}</td></tr>")
        html.append("</table></div>")
        return "\n".join(html)
