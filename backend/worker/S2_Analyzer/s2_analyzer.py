"""
Stage 2: Analyzer (`s2_analyzer.py` -> `Gives meaning to data`)

Takes clean, canonical Process Data (`Tickets, Issues, PRs, Story Points`) directly from Stage 1 Normalizer
in RAM and runs domain-specific mathematical calculations via specialized Math Engines.
"""

from typing import List, Dict, Any, Optional
from backend.domain.process_data_models import NormalizedTicket, NormalizedPR

from .math_engines.time_math import TimeMath
from .math_engines.quality_math import QualityMath
from .burndown_math import BurndownMath


from backend.worker.S0_Extractor.github.utils import detect_sprint_window


class Analyzer:
    """Stage 2: Analyzer Facade. Routes arrays of Process Data to domain-specific Math Engines."""

    @classmethod
    def first_time_yield(cls, tickets: List[NormalizedTicket]) -> float:
        return QualityMath.first_time_yield(tickets)

    @classmethod
    def burndown_curve(
        cls,
        tickets: List[NormalizedTicket],
        start_date_iso: str,
        end_date_iso: str,
        total_ideal_points: Optional[float] = None,
        historical_od: Optional[List[Dict[str, Any]]] = None,
        record_date_iso: Optional[str] = None
    ) -> Dict[str, Any]:
        return BurndownMath.burndown_curve(
            tickets=tickets,
            start_date_iso=start_date_iso,
            end_date_iso=end_date_iso,
            total_ideal_points=total_ideal_points,
            historical_od=historical_od,
            record_date_iso=record_date_iso
        )

    @classmethod
    def prs_per_issue(cls, tickets: List[NormalizedTicket], prs: List[NormalizedPR]) -> float:
        return QualityMath.prs_per_issue(tickets, prs)

    @classmethod
    def sprint_item_timeline(cls, tickets: List[NormalizedTicket], target_sprint: Optional[str] = None) -> List[Dict[str, Any]]:
        return TimeMath.sprint_item_timeline(tickets, target_sprint=target_sprint)

    @classmethod
    def pr_based_fty(cls, prs: List[NormalizedPR]) -> Dict[str, Any]:
        return QualityMath.pr_based_fty(prs)

    @classmethod
    def issue_loop_fty(cls, tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        return QualityMath.issue_loop_fty(tickets)

    @classmethod
    def average_time_in_step(cls, tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        return TimeMath.average_time_in_step(tickets)

    @classmethod
    def sp_breakdown(cls, tickets: List[NormalizedTicket]) -> Dict[str, Any]:
        return QualityMath.sp_breakdown(tickets)

    @classmethod
    def measure_all(
        cls,
        tickets: List[NormalizedTicket],
        prs: List[NormalizedPR],
        record_date: str,
        start_date: str,
        end_date: str,
        kpi_config: Dict[str, Any],
        historical_od: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Master Analyzer entrypoint: runs every mathematical calculation cleanly over RAM process data.
        """
        target_sprint = kpi_config.get("sprint_name")
        if not target_sprint:
            # Auto-detect target sprint from tickets
            raw_dict = [{"fieldValues": [{"fieldName": "Sprint", "value": t.sprint, "startDate": start_date}]} for t in tickets if t.sprint]
            smeta = detect_sprint_window(raw_dict, record_date=record_date) if raw_dict else {}
            target_sprint = smeta.get("sprint_name")

        return {
            "fty_percentage": cls.first_time_yield(tickets),
            "burndown_curve": cls.burndown_curve(
                tickets=tickets,
                start_date_iso=start_date,
                end_date_iso=end_date,
                total_ideal_points=kpi_config.get("total_ideal_points"),
                historical_od=historical_od,
                record_date_iso=record_date
            ),
            "productivity_sliding_window": QualityMath.productivity_sliding_window(tickets, end_date),
            "average_prs_per_issue": cls.prs_per_issue(tickets, prs),
            "sprint_item_timeline": cls.sprint_item_timeline(tickets, target_sprint=target_sprint),
            "pr_based_fty": cls.pr_based_fty(prs),
            "issue_loop_fty": cls.issue_loop_fty(tickets),
            "average_time_in_step": cls.average_time_in_step(tickets),
            "average_time_by_estimate": TimeMath.average_time_by_estimate(tickets),
            "sp_breakdown": cls.sp_breakdown(tickets)
        }
