"""
components.sqdp.sprint_1w_sqdp
===============================
Concrete SQDP widget for **1-week sprint** tracking.

This variant is designed for teams running weekly sprints where each
SQDP letter has 7 cells — one per calendar day (5 working days plus
Saturday and Sunday, or 7 working days depending on team convention).

Inputs
------
A :class:`~models.sqdp_models.SqdpBoardModel` whose letters each
contain up to 7 cells (one per day of the sprint week).

Rendering
---------
Inherits all rendering from :class:`BaseSqdpWidget`.  The only
customisations are:

* **Title** — ``'SQDP Sprint 1 Week'``
* **Per-letter label** — ``'<label> (<char>)'``, e.g. ``'Safety (S)'``.
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QWidget

from components.sqdp.base_sqdp import BaseSqdpWidget
from models.sqdp_models import SqdpBoardModel, SqdpLetterModel


class Sprint1WSqdpWidget(BaseSqdpWidget):
    """SQDP letter-diagram widget for 1-week sprint boards.

    Each letter grid contains up to 7 cells representing one day of the
    sprint.  Five cells typically map to working days; the remaining two
    may represent weekend or buffer days depending on the team's
    configuration.

    Parameters
    ----------
    model : SqdpBoardModel
        Board data with ``time_range='sprint_1w'``.
    parent : QWidget, optional
        Qt parent widget.

    Example
    -------
    >>> from models.sqdp_models import SqdpBoardModel
    >>> widget = Sprint1WSqdpWidget(model=SqdpBoardModel(
    ...     title='Sprint 1W', time_range='sprint_1w', letters=[...]
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
        """Return ``'SQDP Sprint 1 Week'``."""
        return "SQDP Sprint 1 Week"

    def format_label(self, letter: SqdpLetterModel) -> str:
        """Return ``'<label> (<char>)'``, e.g. ``'Safety (S)'``."""
        return f"{letter.label} ({letter.char})"
