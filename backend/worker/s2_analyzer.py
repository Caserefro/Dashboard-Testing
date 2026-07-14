"""
Stage 2: Analyzer (`s2_analyzer.py` -> `Gives meaning to data`)

Takes clean, canonical Process Data (`Tickets, Issues, PRs, Story Points`) directly from Stage 1 Normalizer
in RAM and runs domain-specific mathematical calculations (`First Time Yield > 96%`, `Bigger of: Inverse Root vs remaining`).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math
from backend.models.process_data_models import NormalizedTicket


class Analyzer:
    """Stage 2: Analyzer entity. Computes mathematical KPIs over canonical process data."""

    @staticmethod
    def first_time_yield(tickets: List[NormalizedTicket]) -> float:
        """
        FTY = (Completed Tickets with ZERO Reopen Loops / Total Completed Tickets) * 100.0
        Target: > 96%
        """
        completed = [t for t in tickets if t.status_normalized == "DONE"]
        if not completed:
            return 100.0  # Clean default state when zero tickets are completed yet

        clean_count = sum(1 for t in completed if t.is_first_time_yield)
        fty_raw = (clean_count / len(completed)) * 100.0
        return round(max(0.0, min(100.0, fty_raw)), 2)

    @staticmethod
    def burndown_curve(
        tickets: List[NormalizedTicket],
        start_date_iso: str,
        end_date_iso: str,
        total_ideal_points: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Computes the daily burndown curve series (`remaining_points`, `ideal_points`, `inverse_root_points`).
        Implements `Bigger of: Inverse Root vs remaining`.
        """
        try:
            start_dt = datetime.strptime(start_date_iso[:10], "%Y-%m-%d")
            end_dt = datetime.strptime(end_date_iso[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            start_dt = datetime.now() - timedelta(days=14)
            end_dt = datetime.now()

        total_days = max(1, (end_dt - start_dt).days)

        if total_ideal_points is None or total_ideal_points <= 0:
            total_ideal_points = sum(t.story_points for t in tickets) if tickets else 100.0

        series: List[Dict[str, Any]] = []

        for day_offset in range(total_days + 1):
            current_dt = start_dt + timedelta(days=day_offset)
            current_date_str = current_dt.strftime("%Y-%m-%d")

            daily_completed = sum(
                t.story_points for t in tickets
                if t.status_normalized == "DONE" and t.completed_date and t.completed_date <= current_date_str
            )

            remaining = max(0.0, total_ideal_points - daily_completed)
            ideal = max(0.0, total_ideal_points * (1.0 - day_offset / total_days))
            inv_root = max(0.0, total_ideal_points * (1.0 - math.sqrt(day_offset / total_days)))

            series.append({
                "date": current_date_str,
                "remaining_points": round(remaining, 2),
                "ideal_points": round(ideal, 2),
                "inverse_root_points": round(inv_root, 2),
            })

        return series

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

    @classmethod
    def measure_all(
        cls,
        tickets: List[NormalizedTicket],
        start_date: str,
        end_date: str,
        kpi_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Master Analyzer entrypoint: runs every mathematical calculation cleanly over RAM process data.
        """
        return {
            "fty_percentage": cls.first_time_yield(tickets),
            "burndown_curve": cls.burndown_curve(
                tickets=tickets,
                start_date_iso=start_date,
                end_date_iso=end_date,
                total_ideal_points=kpi_config.get("total_ideal_points"),
            ),
            "tickets_per_day_chart": cls.tickets_per_day(tickets),
        }
