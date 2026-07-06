"""
components.sqdp.sprint_2w_sqdp
===============================
Concrete SQDP widget for **sprints per quarter** tracking (fiscal week based system).

This variant is designed for teams running sprint/weekly boards across a fiscal quarter,
where each SQDP letter has exactly 13 blocks — representing the 13 sprints/weeks in a quarter.

Inputs
------
A :class:`~models.sqdp_models.SqdpBoardModel` whose letters each
contain 13 cells (one per week/sprint of the fiscal quarter).

Rendering
---------
Inherits all rendering from :class:`BaseSqdpWidget`.  The only
customisations are:

* **Title** — ``'SQDP Sprints / Quarter (13 Weeks)'``
* **Per-letter label** — ``'<label> (<char>)'``, e.g. ``'Quality (Q)'``.
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QWidget

from components.sqdp.base_sqdp import BaseSqdpWidget
from models.sqdp_models import SqdpBoardModel, SqdpLetterModel


class Sprint2WSqdpWidget(BaseSqdpWidget):
    """SQDP letter-diagram widget for 13-sprint/quarter boards (fiscal week system).

    Each letter grid contains exactly 13 cells representing the 13 sprints/weeks
    of the fiscal quarter.

    Parameters
    ----------
    model : SqdpBoardModel
        Board data with ``time_range='sprint_2w'``.
    parent : QWidget, optional
        Qt parent widget.

    Example
    -------
    >>> from models.sqdp_models import SqdpBoardModel
    >>> widget = Sprint2WSqdpWidget(model=SqdpBoardModel(
    ...     title='SQDP Sprints / Quarter', time_range='sprint_2w', letters=[...]
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
        """Return ``'SQDP Sprints / Quarter (13 Weeks)'``."""
        return "SQDP Sprints / Quarter (13 Weeks)"

    def format_label(self, letter: SqdpLetterModel) -> str:
        """Return ``'<label> (<char>)'``, e.g. ``'Quality (Q)'``."""
        return f"{letter.label} ({letter.char})"

