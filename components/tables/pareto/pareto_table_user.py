"""
components.tables.pareto.pareto_table_user
==========================================
User-input Pareto table with current-week highlighting.

Purpose
-------
Extends the read-only :class:`ParetoTable` with visual affordances for
data entry.  The *current week* column is highlighted with a subtle
blue tint and each editable cell shows a small pencil/edit icon so the
user knows where to input their daily loss counts.

This widget is for **user submission of daily loss counts**.  It performs
no validation or business logic — it only paints the visual indicators.

Extra rendering
---------------
* Current-week column receives a light blue background (``ACCENT_BLUE``
  at 25 % opacity) drawn over the normal alternating-row colour.
* A 6 × 6 px pencil glyph is painted in the bottom-right corner of each
  editable cell via :meth:`_draw_input_indicator`.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

from components.theme import ACCENT_BLUE, GRID_LINE, HEADER_CLR, BG_WHITE, TBL_ALT_ROW
from components.tables.pareto.pareto_table import ParetoTable, ParetoTableModel

# Subtle blue overlay for the editable column
_EDIT_HIGHLIGHT = QColor(ACCENT_BLUE)
_EDIT_HIGHLIGHT.setAlpha(25)

_PENCIL_CLR = QColor("#90CAF9")
_DATA_FONT = QFont("Segoe UI", 8)


class ParetoTableUser(ParetoTable):
    """User-input Pareto table for submission of daily loss counts.

    Inherits from :class:`ParetoTable` and adds:

    * A highlighted *current week* column with a blue tint to indicate
      editable cells.
    * A pencil/edit icon in every editable cell.

    Parameters
    ----------
    model : ParetoTableModel
        Initial table data.
    current_week_index : int
        Zero-based index into ``model.columns`` identifying the column
        that should be highlighted as the current (editable) week.
        Defaults to the last column.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        model: ParetoTableModel,
        current_week_index: int = -1,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(model, parent)
        self._current_week_index: int = current_week_index

    @property
    def current_week_index(self) -> int:
        """Resolved zero-based index of the editable column."""
        idx = self._current_week_index
        if idx < 0:
            idx = len(self.model.columns) + idx
        return max(0, min(idx, len(self.model.columns) - 1))

    # ── rendering ───────────────────────────────────────────────
    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the Pareto table, then overlay the current-week highlight."""
        m = self.model
        if not m.categories:
            return

        # Let the parent draw the base table first.
        super().paint_table(painter, inner)

        # Now overlay the current-week column highlight + edit icons.
        n_data_cols = len(m.columns) + 1
        n_rows = 1 + len(m.categories)
        cat_w, dat_w, row_h = self._calc_layout(inner, n_data_cols, n_rows)

        tx, ty = inner.x(), inner.y()
        cw_idx = self.current_week_index
        cw_x = tx + cat_w + cw_idx * dat_w

        for i in range(len(m.categories)):
            ry = ty + (i + 1) * row_h
            cell = QRectF(cw_x, ry, dat_w, row_h)

            # Blue highlight overlay
            painter.setBrush(_EDIT_HIGHLIGHT)
            painter.setPen(Qt.NoPen)
            painter.drawRect(cell)

            # Edit indicator icon
            self._draw_input_indicator(painter, cell)

    # ── edit icon ───────────────────────────────────────────────
    @staticmethod
    def _draw_input_indicator(p: QPainter, rect: QRectF) -> None:
        """Draw a small pencil/edit glyph in the bottom-right of *rect*.

        The glyph is a 6 × 6 px stylised pencil rendered with two
        strokes — a diagonal line (the pencil body) and a small
        triangle tip.

        Parameters
        ----------
        p : QPainter
            Active painter.
        rect : QRectF
            The cell rectangle in which the icon is placed.
        """
        size = 6.0
        margin = 3.0
        bx = rect.right() - size - margin
        by = rect.bottom() - size - margin

        pen = QPen(_PENCIL_CLR, 1.2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        # Pencil body (diagonal)
        p.drawLine(
            int(bx + 1), int(by + size - 1),
            int(bx + size - 1), int(by + 1),
        )
        # Pencil tip (small dot)
        p.drawPoint(int(bx), int(by + size))
