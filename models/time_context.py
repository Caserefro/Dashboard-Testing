"""Time context domain model representing a validated period of time."""

from dataclasses import dataclass
from typing import List
from .query_models import PeriodQueryModel


@dataclass(frozen=True)
class TimeSpanContext:
    """Structured domain entity representing an active, validated time period.

    Subscribed widgets receive this entity via the ``TimePeriodRegistry``
    and adapt their X-axis, labels, and datasets autonomously.

    Attributes:
        granularity: Temporal mode ('Fiscal Weeks', 'Days', 'Sprints').
        window_label: Display label for the period (e.g., 'Q1 (Weeks 1–13)').
        fiscal_year: Selected fiscal year (e.g., 'FY 2026').
        valid_sub_intervals: Sub-axis tick categories aligned with the period.
        is_sprint_capable: True if sprint tracking (like Burndown) is valid.
        team_scope: Selected team or cell (e.g., 'Cell 4 (Assembly)').
    """
    granularity: str
    window_label: str
    fiscal_year: str
    valid_sub_intervals: List[str]
    is_sprint_capable: bool
    team_scope: str

    @classmethod
    def from_query(cls, query: PeriodQueryModel) -> "TimeSpanContext":
        """Construct a validated TimeSpanContext from a raw PeriodQueryModel."""
        granularity = query.granularity
        window_label = query.period_window
        fiscal_year = query.fiscal_year
        team_scope = query.team_selection

        # Determine capabilities and sub-intervals based on granularity
        if granularity == "Fiscal Weeks":
            is_sprint_capable = True
            # For Q1..Q4, generate week categories based on window
            if "Q1" in window_label:
                valid_sub_intervals = ["W1", "W3", "W5", "W7", "W9", "W11", "W13"]
            elif "Q2" in window_label:
                valid_sub_intervals = ["W14", "W16", "W18", "W20", "W22", "W24", "W26"]
            elif "Q3" in window_label:
                valid_sub_intervals = ["W27", "W29", "W31", "W33", "W35", "W37", "W39"]
            elif "Q4" in window_label:
                valid_sub_intervals = ["W40", "W42", "W44", "W46", "W48", "W50", "W52"]
            else:
                valid_sub_intervals = ["W1", "W2", "W3", "W4", "W5", "W6", "W7"]
        elif granularity == "Days":
            is_sprint_capable = False
            valid_sub_intervals = ["Day 1", "Day 6", "Day 12", "Day 18", "Day 24", "Day 31"]
        else:
            is_sprint_capable = True
            valid_sub_intervals = ["Day 1", "Day 4", "Day 7", "Day 10", "Day 14"]

        return cls(
            granularity=granularity,
            window_label=window_label,
            fiscal_year=fiscal_year,
            valid_sub_intervals=valid_sub_intervals,
            is_sprint_capable=is_sprint_capable,
            team_scope=team_scope,
        )
