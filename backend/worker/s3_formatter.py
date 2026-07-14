"""
Stage 3: Formatter (`s3_formatter.py` -> `Gives Shape to data`)

Receives raw numerical metrics from Stage 2 Analyzer and shapes them strictly into the output contracts:
1. `Graphic contract` (`ui_graph_contracts` format for Data Sync Endpoint & Visual Layer Qt charts).
2. `HTML` (For web rendering or email summary reports).
3. `CSV` (For tabular export or spreadsheet ingestion).

Enforces all bounds (0.0-100.0, ISO-8601 dates, correct key names) right before `sys.stdout`.
"""

from typing import Dict, Any, List
import csv
import io


class Formatter:
    """Stage 3: Formatter entity. Enforces output boundaries and packages the exact dictionary for sys.stdout."""

    @staticmethod
    def to_graphic_contract(computed_kpis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shapes KPIs into the exact `ui_graph_contracts.json` specification.
        Enforces all contract bounds (0.0 - 100.0, ISO dates) before returning to Data Sync.
        """
        # 1. First Time Yield Gauge
        fty_raw = float(computed_kpis.get("fty_percentage", 100.0))
        fty_bounded = round(max(0.0, min(100.0, fty_raw)), 2)

        # 2. Burndown Curve
        burndown_contract: List[Dict[str, Any]] = []
        for pt in computed_kpis.get("burndown_curve", []):
            burndown_contract.append({
                "date": str(pt.get("date", ""))[:10],
                "remaining_points": round(max(0.0, float(pt.get("remaining_points", 0.0))), 2),
                "ideal_points": round(max(0.0, float(pt.get("ideal_points", 0.0))), 2),
                "inverse_root_points": round(max(0.0, float(pt.get("inverse_root_points", 0.0))), 2),
            })

        # 3. Tickets Per Day Chart
        velocity_contract: List[Dict[str, Any]] = []
        for row in computed_kpis.get("tickets_per_day_chart", []):
            velocity_contract.append({
                "day_label": str(row.get("day_label", "Day")),
                "tickets_merged": max(0, int(row.get("tickets_merged", 0))),
            })

        return {
            "first_time_yield_gauge": {"fty_percentage": fty_bounded},
            "burndown_curve": burndown_contract,
            "tickets_per_day_chart": velocity_contract,
        }

    @staticmethod
    def to_csv(computed_kpis: Dict[str, Any]) -> str:
        """Shapes computed KPIs into a clean CSV table string."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Metric Summary", "Value"])
        writer.writerow(["First Time Yield (%)", computed_kpis.get("fty_percentage", 100.0)])
        writer.writerow([])

        writer.writerow(["Burndown Curve"])
        writer.writerow(["Date", "Remaining Points", "Ideal Points", "Inverse Root Points"])
        for pt in computed_kpis.get("burndown_curve", []):
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

    @staticmethod
    def to_html(computed_kpis: Dict[str, Any]) -> str:
        """Shapes computed KPIs into a clean HTML summary card."""
        fty = computed_kpis.get("fty_percentage", 100.0)
        html = [
            "<div style='font-family: Arial, sans-serif; padding: 16px; border: 1px solid #ccc; border-radius: 8px;'>",
            f"<h2 style='color: #1565c0;'>Project ATLAS - Worker Report</h2>",
            f"<p><strong>First Time Yield (FTY):</strong> <span style='color: #2e7d32; font-size: 1.2em;'>{fty}%</span></p>",
            "<h3>Burndown Daily Series</h3>",
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>",
            "<tr style='background-color: #f5f5f5;'><th>Date</th><th>Remaining</th><th>Ideal</th></tr>",
        ]
        for pt in computed_kpis.get("burndown_curve", []):
            html.append(
                f"<tr><td>{pt.get('date')}</td><td>{pt.get('remaining_points')}</td><td>{pt.get('ideal_points')}</td></tr>")
        html.append("</table></div>")
        return "\n".join(html)

    @classmethod
    def format_all(
            cls,
            board_id: int,
            record_date: str,
            computed_kpis: Dict[str, Any],
            tickets: List[Any],
            total_ideal_points: Any,
            output_format: str = "graphic_contract",
            prs: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Master Stage 3 Formatter entrypoint (`Gives Shape to Data`).
        Takes computed KPIs and process data, shaping them into the exact 2-part dictionary
        output contract (`kpi_record_for_db` + `graphic_contract`) right before sys.stdout.
        """
        from backend.models.process_data_models import ProcessDataAggregate

        aggregate_record = ProcessDataAggregate.create_from_items(
            board_id=board_id,
            record_date=record_date,
            tickets=tickets,
            prs=prs or [],
            issues=[],
            total_ideal_points=total_ideal_points
        )

        response: Dict[str, Any] = {
            "board_id": board_id,
            "record_date": record_date,
            "kpi_record_for_db": aggregate_record.to_dict(),
        }

        if output_format == "csv":
            response["csv_output"] = cls.to_csv(computed_kpis)
        elif output_format == "html":
            response["html_output"] = cls.to_html(computed_kpis)
        else:
            response["graphic_contract"] = cls.to_graphic_contract(computed_kpis)

        return response
