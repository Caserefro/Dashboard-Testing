"""
components.tables.safety.safety_table_user
==========================================
Safety table for user submission of safety concerns.

Purpose
-------
Extends the read-only :class:`SafetyTable` with visual cues that guide
the user toward completing required data entry.  Any field whose
``field_value`` is empty is highlighted with a yellow warning background,
and editable cells display a small pencil icon to indicate where input
is expected.

This widget performs **no** validation logic — it simply renders the
visual indicators based on the current model state.

Extra rendering
---------------
* Empty/unfilled ``field_value`` cells receive a ``#FFF9C4`` (light
  yellow) background as a warning.
* A 6 × 6 px pencil glyph is painted in the bottom-right corner of
  every editable cell (``field_value`` and ``comment`` columns).
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

from components.theme import GRID_LINE, HEADER_CLR, BG_WHITE, TBL_ALT_ROW
from components.tables.safety.safety_table import SafetyTable, SafetyTableModel

_WARN_BG = QColor("#FFF9C4")  # light yellow for unfilled fields
_PENCIL_CLR = QColor("#90CAF9")
_DATA_FONT = QFont("Segoe UI", 8)

# Column layout ratios (must match SafetyTable._COL_RATIOS)
_COL_RATIOS = (0.25, 0.20, 0.20, 0.35)
_MAX_ROW_H = 26


class SafetyTableUser(SafetyTable):
    """Safety table for user submission of safety concerns.

    Inherits from :class:`SafetyTable` and adds:

    * **Yellow warning background** on any ``field_value`` cell that is
      empty or whitespace-only.
    * **Pencil/edit icons** on the *Value* and *Comment* columns to
      indicate editable cells.

    Parameters
    ----------
    model : SafetyTableModel
        Initial table data.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        model: SafetyTableModel,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(model, parent)

    # ── rendering ───────────────────────────────────────────────
    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the base table, then overlay warning highlights and icons."""
        # Draw the base safety table first
        super().paint_table(painter, inner)

        m = self.model
        if not m.fields:
            return

        n_rows = 2 + len(m.fields)
        row_h = min(inner.height() / max(n_rows, 1), _MAX_ROW_H)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        for i, fld in enumerate(m.fields):
            ry = ty + (i + 2) * row_h  # +2 for header + sub-header

            # Value column (index 1): highlight if empty
            val_x = tx + widths[0]
            val_cell = QRectF(val_x, ry, widths[1], row_h)
            if not fld.field_value.strip():
                self._draw_warning_cell(painter, val_cell)

            # Edit indicators on Value and Comment columns
            self._draw_input_indicator(painter, val_cell)

            comment_x = tx + widths[0] + widths[1] + widths[2]
            comment_cell = QRectF(comment_x, ry, widths[3], row_h)
            if not fld.comment.strip():
                self._draw_warning_cell(painter, comment_cell)
            self._draw_input_indicator(painter, comment_cell)

    # ── warning highlight ───────────────────────────────────────
    @staticmethod
    def _draw_warning_cell(p: QPainter, rect: QRectF) -> None:
        """Overlay a yellow warning background on *rect*.

        Parameters
        ----------
        p : QPainter
            Active painter.
        rect : QRectF
            Cell bounding rectangle to highlight.
        """
        p.setBrush(_WARN_BG)
        p.setPen(QPen(GRID_LINE, 0.8))
        p.drawRect(rect)

    # ── edit icon ───────────────────────────────────────────────
    @staticmethod
    def _draw_input_indicator(p: QPainter, rect: QRectF) -> None:
        """Draw a small pencil/edit glyph in the bottom-right of *rect*.

        The glyph is a 6 × 6 px stylised pencil rendered with two
        strokes — a diagonal line (the pencil body) and a small point
        (the tip).

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
        # Pencil tip
        p.drawPoint(int(bx), int(by + size))
