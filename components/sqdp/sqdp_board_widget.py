"""Unified SQDP Board Widget supporting multi-granularity rendering.

Dynamically adapts between 13-column (Fiscal Weeks/Quarter) and 31-column
(Daily/Month) representations based on the active TimeSpanContext.
"""

from __future__ import annotations
from typing import Optional

from PyQt5.QtWidgets import QWidget

from components.sqdp.base_sqdp import BaseSqdpWidget
from components.mixins import TimeAware
from models.sqdp_models import SqdpBoardModel, SqdpLetterModel
from models.time_context import TimeSpanContext


class SqdpBoardWidget(BaseSqdpWidget, TimeAware):
    """Unified SQDP board graphic widget supporting both 13-cell and 31-cell modes.

    When subscribed to `TimePeriodRegistry` via `TimeAware`, this widget automatically
    adjusts its grid dimensions and labels depending on the selected granularity:
    - Days / Month: 31 cells per letter (`Day 1..31`)
    - Fiscal Weeks / Quarter: 13 cells per letter (`Week 1..13`)
    """

    def __init__(
        self,
        model: SqdpBoardModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(model, parent)

    def get_title(self) -> str:
        """Return the dynamic title from the current model."""
        return self.model.title

    def format_label(self, letter: SqdpLetterModel) -> str:
        """Format label based on active grid capacity (`Day X` vs `Week / Sprint char`)."""
        if self.model.time_range == "daily" or len(letter.cells) > 15:
            return f"{letter.label} - Day {len(letter.cells)}"
        return f"{letter.label} ({letter.char})"

    def on_time_period_changed(self, ctx: TimeSpanContext) -> None:
        """Subscriber Slot: autonomously adapt between 31-cell daily and 13-cell weekly/quarter boards."""
        from tools.component_gallery import generate_sqdp_board
        time_range = "daily" if ctx.granularity in ("Days", "Months") else "sprint_2w"
        new_model = generate_sqdp_board(time_range)
        new_model.title = f"SQDP Board — {ctx.team_scope} ({ctx.window_label})"
        self.set_data(new_model)
