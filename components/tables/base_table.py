"""
components.tables.base_table
=============================
Abstract base class for all table graphic components.

Purpose
-------
Provides shared layout calculation, cell-drawing helpers, and a
consistent rendering pipeline for every table widget in the dashboard.
Concrete subclasses implement :meth:`paint_table` which receives the
inner content rectangle after the card background has already been drawn.

Rendering contract
------------------
* ``paint_content()`` (from :class:`BaseGraphicWidget`) delegates to
  ``paint_table(painter, inner_rect)`` which **must** be overridden.
* All colours are imported from :mod:`components.theme` so every table
  automatically respects the global palette.

Helper methods
--------------
``_draw_header_cell(p, rect, text)``
    Fills *rect* with ``TBL_HDR_BG`` and renders centred white text.
    Use for column-header and title cells.

``_draw_data_cell(p, rect, text, row_index)``
    Alternates between ``BG_WHITE`` (even rows) and ``TBL_ALT_ROW``
    (odd rows) and renders centred dark text.

``_calc_layout(inner_rect, n_cols, n_rows, cat_col_ratio)``
    Returns *(cat_col_w, data_col_w, row_h)* — the width of the
    category column, the uniform width of each data column, and the
    clamped row height (max 26 px).
"""

from __future__ import annotations

import abc
from typing import Any, Optional, Tuple, TypeVar

from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

from components.base import BaseGraphicWidget
from components.theme import (
    HEADER_CLR,
    TEXT_WHITE,
    BG_WHITE,
    GRID_LINE,
    TBL_HDR_BG,
    TBL_ALT_ROW,
)

T = TypeVar("T")

# Internal constants
_HDR_BORDER_CLR = QColor("#0D47A1")
_HDR_FONT = QFont("Segoe UI", 8, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 8)
_CAT_FONT = QFont("Segoe UI", 8, QFont.Bold)
_MAX_ROW_H = 26


class BaseTableWidget(BaseGraphicWidget[T]):
    """Abstract base for all dashboard table widgets.

    Type Parameters
    ---------------
    T : dataclass
        The typed DTO that carries table data (e.g. ``ParetoTableModel``
        or ``SafetyTableModel``).

    Parameters
    ----------
    model : T
        The initial data model for rendering.
    parent : QWidget, optional
        Parent widget in the Qt object tree.
    """

    def __init__(self, model: T, parent: Optional[Any] = None) -> None:
        super().__init__(model, parent)

    # ── abstract ────────────────────────────────────────────────
    @abc.abstractmethod
    def paint_table(self, painter: QPainter, inner_rect: QRectF) -> None:
        """Paint the full table inside *inner_rect*.

        Called by :meth:`paint_content`.  Implementations should use the
        ``_draw_*`` helpers and ``_calc_layout`` for consistency.
        """

    # ── pipeline glue ───────────────────────────────────────────
    def paint_content(self, painter: QPainter, inner_rect: QRectF) -> None:
        """Delegates to :meth:`paint_table`."""
        self.paint_table(painter, inner_rect)

    # ── layout helper ───────────────────────────────────────────
    @staticmethod
    def _calc_layout(
        inner_rect: QRectF,
        n_cols: int,
        n_rows: int,
        cat_col_ratio: float = 0.30,
    ) -> Tuple[float, float, float]:
        """Calculate column widths and row height for a uniform grid.

        Parameters
        ----------
        inner_rect : QRectF
            The drawable area inside the card.
        n_cols : int
            Number of *data* columns (excluding the category column).
        n_rows : int
            Total number of rows including the header row.
        cat_col_ratio : float
            Fraction of total width devoted to the category column
            (default 0.30 = 30 %).

        Returns
        -------
        tuple[float, float, float]
            ``(cat_col_w, data_col_w, row_h)``
        """
        cat_col_w = inner_rect.width() * cat_col_ratio
        data_col_w = (inner_rect.width() - cat_col_w) / max(n_cols, 1)
        row_h = min(inner_rect.height() / max(n_rows, 1), _MAX_ROW_H)
        return cat_col_w, data_col_w, row_h

    # ── cell-drawing helpers ────────────────────────────────────
    @staticmethod
    def _draw_header_cell(
        p: QPainter,
        rect: QRectF,
        text: str,
        align: int = Qt.AlignCenter,
    ) -> None:
        """Draw a header cell with ``TBL_HDR_BG`` background and white text.

        Parameters
        ----------
        p : QPainter
            Active painter (caller manages begin/end).
        rect : QRectF
            Cell bounding rectangle.
        text : str
            Label to render.
        align : int
            Qt alignment flags (default centred).
        """
        p.setFont(_HDR_FONT)
        p.setBrush(TBL_HDR_BG)
        p.setPen(QPen(_HDR_BORDER_CLR, 1))
        p.drawRect(rect)
        p.setPen(TEXT_WHITE)
        if align & Qt.AlignLeft:
            p.drawText(rect.adjusted(6, 0, 0, 0), align | Qt.AlignVCenter, text)
        else:
            p.drawText(rect, align | Qt.AlignVCenter, text)

    @staticmethod
    def _draw_data_cell(
        p: QPainter,
        rect: QRectF,
        text: str,
        row_index: int,
        *,
        bold: bool = False,
        align: int = Qt.AlignCenter,
    ) -> None:
        """Draw a data cell with alternating row background.

        Parameters
        ----------
        p : QPainter
            Active painter.
        rect : QRectF
            Cell bounding rectangle.
        text : str
            Value to render.
        row_index : int
            Zero-based row index — even rows use ``BG_WHITE``, odd rows
            use ``TBL_ALT_ROW``.
        bold : bool
            If *True* the text is rendered in bold (useful for category
            labels).
        align : int
            Qt alignment flags (default centred).
        """
        row_bg = BG_WHITE if row_index % 2 == 0 else TBL_ALT_ROW
        p.setBrush(row_bg)
        p.setPen(QPen(GRID_LINE, 0.8))
        p.drawRect(rect)
        p.setFont(_CAT_FONT if bold else _DATA_FONT)
        p.setPen(HEADER_CLR)
        if align & Qt.AlignLeft:
            p.drawText(rect.adjusted(6, 0, 0, 0), align | Qt.AlignVCenter, text)
        else:
            p.drawText(rect, align | Qt.AlignVCenter, text)
