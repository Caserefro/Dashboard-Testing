"""
Stage 3: Formatter (`s3_formatter.py` -> `Gives Shape to data`)

Receives raw numerical metrics from Stage 2 Analyzer and shapes them strictly into the output contracts via specific formatters:
1. `SpreadsheetFormatter` (For Data Sync Endpoint & Visual Layer Qt charts).
2. `HtmlFormatter` (For web rendering or email summary reports).
3. `CsvFormatter` (For tabular export).

Enforces all bounds (0.0-100.0, ISO-8601 dates, correct key names) right before `sys.stdout`.
"""

from typing import Dict, Any, List

from .formatters.spreadsheet_formatter import SpreadsheetFormatter
from .formatters.csv_formatter import CsvFormatter
from .formatters.html_formatter import HtmlFormatter


class Formatter:
    """Stage 3: Formatter Facade. Routes computed KPIs to the requested output format strategy."""

    @staticmethod
    def to_spreadsheet_contract(computed_kpis: Dict[str, Any]) -> Dict[str, Any]:
        return SpreadsheetFormatter.format(computed_kpis)

    @staticmethod
    def to_csv(computed_kpis: Dict[str, Any]) -> str:
        return CsvFormatter.format(computed_kpis)

    @staticmethod
    def to_html(computed_kpis: Dict[str, Any]) -> str:
        return HtmlFormatter.format(computed_kpis)

    @classmethod
    def format_all(
            cls,
            board_id: int,
            record_date: str,
            computed_kpis: Dict[str, Any],
            tickets: List[Any],
            total_ideal_points: Any,
            prs: List[Any] = None,
            output_format: str = "graphic_contract",
            project_config: Dict[str, Any] = None
    ) -> str:
        import json
        from backend.domain.process_data_models import ProcessDataAggregate

        # Calculate required DB payload properties
        completed_sp = sum(t.story_points for t in tickets if t.status_normalized == "DONE") if tickets else 0.0
        total_sp = total_ideal_points if total_ideal_points else (sum(t.story_points for t in tickets) if tickets else 100.0)
        remaining_sp = max(0.0, total_sp - completed_sp)
        
        completed_tickets = [t for t in tickets if t.status_normalized == "DONE"] if tickets else []
        clean_tickets = sum(1 for t in completed_tickets if t.is_first_time_yield)
        prs_merged = sum(1 for p in (prs or []) if p.status_normalized == "MERGED")

        agg = ProcessDataAggregate(
            board_id=board_id,
            record_date=record_date,
            total_story_points=total_sp,
            completed_story_points=completed_sp,
            remaining_story_points=remaining_sp,
            total_completed_tickets=len(completed_tickets),
            first_time_yield_clean_tickets=clean_tickets,
            prs_merged_count=prs_merged
        )

        db_record = agg.to_dict()

        # Route to the correct strategy based on desired output format
        if output_format == "csv":
            formatted_output = cls.to_csv(computed_kpis)
        elif output_format == "html":
            formatted_output = cls.to_html(computed_kpis)
        else:
            # Default to spreadsheet/graphic contract
            contract_dict = cls.to_spreadsheet_contract(computed_kpis)
            formatted_output = json.dumps(contract_dict)

        final_payload = {
            "board_id": board_id,
            "kpi_record_for_db": db_record,
            "graphic_contract": formatted_output
        }
        return final_payload
