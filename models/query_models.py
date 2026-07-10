"""Query models for dashboard filtering and time span requests.

Pure dataclass DTOs with zero Qt dependencies or UI references.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PeriodQueryModel:
    """Immutable query data model emitted by PeriodFilterWidget when updated.

    Attributes:
        granularity: 'Fiscal Weeks', 'Days', or 'Months'.
        period_window: e.g., 'Q3 (Weeks 27–39)' or 'July (Days 1–31)'.
        fiscal_year: e.g., 'FY 2026'.
        team_selection: e.g., 'Cell 4 (Assembly)' or 'Lobby: XR9-8B2'.
        room_code: Optional 6-8 char room code if joined via Among Us style room code.
    """
    granularity: str
    period_window: str
    fiscal_year: str
    team_selection: str
    room_code: Optional[str] = None
