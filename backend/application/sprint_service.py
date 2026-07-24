"""
Sprint Calendar Service (`backend/application/sprint_service.py`)

Application layer services for sprint boundary identification and Excel calendar generation.
Adheres strictly to SOLID principles:
- SRP: Base SprintCalendarService manages sprint date boundaries; ExcelSprintCalendarService shapes Excel 2-column table skeletons.
- OCP: Easily extensible for other calendar formats (Smartsheet, Web UI Gantt) without modifying base GraphQL extraction.
- LSP: ExcelSprintCalendarService can be substituted wherever SprintCalendarService is expected.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from backend.AnalyticsWorkerFactory.S0_Extractor.github.github_extractor import GitHubExtractor
from backend.AnalyticsWorkerFactory.S0_Extractor.github.utils import detect_sprint_window


@dataclass
class SprintInfo:
    title: str
    start_date: str
    end_date: str
    duration: int
    total_ideal_points: float = 0.0
    is_completed: bool = False


class SprintCalendarService:
    """
    Base Application Service for identifying sprint boundaries via GitHub GraphQL or payload inspection.
    """

    def calculate_end_date(self, start_date_str: str, duration_days: int) -> str:
        """Calculates end_date as (start_date + duration days)."""
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=duration_days)
            return end_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return start_date_str

    def get_sprints_via_graphql(self, payload: Dict[str, Any]) -> List[SprintInfo]:
        """
        Queries GitHub GraphQL API directly for official ProjectV2 iteration field settings.
        Returns a list of structured SprintInfo objects with computed end_date.
        """
        raw_sprints = GitHubExtractor.fetch_project_sprints(payload)
        sprint_info_list = []

        for item in raw_sprints:
            start_date = item.get("start_date", "")
            duration = item.get("duration", 14)
            end_date = self.calculate_end_date(start_date, duration) if start_date else ""

            sprint_info_list.append(
                SprintInfo(
                    title=item.get("title", "Unknown Sprint"),
                    start_date=start_date,
                    end_date=end_date,
                    duration=duration,
                    is_completed=item.get("is_completed", False)
                )
            )

        return sprint_info_list

    def get_sprint_from_work_items(self, work_items: List[Dict[str, Any]]) -> SprintInfo:
        """
        Fallback / payload inspection method reusing Extractor's detect_sprint_window helper.
        """
        meta = detect_sprint_window(work_items)
        sname = meta.get("sprint_name") or "Sprint 1"
        sdate = meta.get("start_date") or "2026-07-01"
        edate = meta.get("end_date") or "2026-07-14"
        sp = meta.get("total_ideal_points") or 0.0

        return SprintInfo(
            title=sname,
            start_date=sdate,
            end_date=edate,
            duration=14,
            total_ideal_points=sp
        )


class ExcelSprintCalendarService(SprintCalendarService):
    """
    Excel-specific Application Service extending SprintCalendarService.
    Generates 2-column table skeleton rows (record_date, Sprint) for Excel tables.
    """

    def generate_excel_calendar_rows(self, sprint: SprintInfo) -> List[Tuple[str, str]]:
        """
        Generates day-by-day (record_date, Sprint) pairs for the given sprint date window.
        Returns e.g. [("2026-07-21", "Sprint 1"), ("2026-07-22", "Sprint 1"), ...].
        """
        if not sprint.start_date:
            return []

        try:
            start_dt = datetime.strptime(sprint.start_date, "%Y-%m-%d")
        except ValueError:
            return []

        rows = []
        for day_offset in range(sprint.duration + 1):
            curr_dt = start_dt + timedelta(days=day_offset)
            date_str = curr_dt.strftime("%Y-%m-%d")
            rows.append((date_str, sprint.title))

        return rows
