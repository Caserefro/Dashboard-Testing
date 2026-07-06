"""
components.sqdp.daily_sqdp
===========================
Concrete SQDP widget for **daily** tracking.

This variant is designed for teams that track each calendar day
individually.  Each SQDP letter can contain up to 31 cells — one
per day of the month.  The larger grid sizes mean the renderer
automatically scales cell sizes down to fit the available space.

Inputs
------
A :class:`~models.sqdp_models.SqdpBoardModel` whose letters each
contain up to 31 cells (one per calendar day).

Rendering
---------
Inherits all rendering from :class:`BaseSqdpWidget`.  The only
customisations are:

* **Title** — ``'SQDP Daily'``
* **Per-letter label** — ``'<label> - Day <n>'`` where *n* is the
  total number of cells in that letter's grid.
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QWidget

from components.sqdp.base_sqdp import BaseSqdpWidget
from models.sqdp_models import SqdpBoardModel, SqdpLetterModel


class DailySqdpWidget(BaseSqdpWidget):
    """SQDP letter-diagram widget for daily (monthly) boards.

    Each letter grid may contain up to 31 cells — one per calendar day
    in the current month.  The cell size is automatically scaled so that
    the larger grids fit comfortably within the card.

    Parameters
    ----------
    model : SqdpBoardModel
        Board data with ``time_range='daily'``.
    parent : QWidget, optional
        Qt parent widget.

    Example
    -------
    >>> from models.sqdp_models import SqdpBoardModel
    >>> widget = DailySqdpWidget(model=SqdpBoardModel(
    ...     title='Daily SQDP', time_range='daily', letters=[...]
    ... ))
    """

    def __init__(
        self,
        model: SqdpBoardModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(model, parent)

    # ── hook implementations ───────────────────────────────────
    def get_title(self) -> str:
        """Return ``'SQDP Daily'``."""
        return "SQDP Daily"

    def format_label(self, letter: SqdpLetterModel) -> str:
        """Return ``'<label> - Day <n>'``, e.g. ``'Safety - Day 31'``."""
        return f"{letter.label} - Day {len(letter.cells)}"
