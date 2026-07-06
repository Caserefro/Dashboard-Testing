"""
components.tables.safety.safety_table
=====================================
Read-only safety metrics table for the dashboard display.

Purpose
-------
Renders a table of safety fields grouped by category, with an optional
sub-header showing the *principal* name.  Each
:class:`SafetyFieldModel` row shows ``field_name``, ``field_value``,
a coloured *category badge*, and an optional ``comment``.

This widget performs **zero** business logic.

Data model
----------
.. code-block:: python

    @dataclass
    class SafetyFieldModel:
        field_name: str
        field_value: str
        category: str
        comment: str = ''

    @dataclass
    class SafetyTableModel:
        title: str
        principal: str
        categories: List[str]
        fields: List[SafetyFieldModel] = field(default_factory=list)

Rendering
---------
1. **Header row** – four columns: *Field*, *Value*, *Category*, *Comment*.
2. **Principal sub-header** – a single spanning row with the principal's
   name on a light-grey background.
3. **Data rows** – one row per ``SafetyFieldModel``.  The *Category*
   cell renders a small coloured badge/tag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

from components.theme import (
    HEADER_CLR,
    TEXT_WHITE,
    BG_WHITE,
    GRID_LINE,
    TBL_HDR_BG,
    TBL_ALT_ROW,
    ACCENT_BLUE,
    GREEN,
    ORANGE,
    RED,
    NAVY,
    SUBTEXT,
)
from components.tables.base_table import BaseTableWidget


# ── data models ─────────────────────────────────────────────────
@dataclass
class SafetyFieldModel:
    """Single safety metric row.

    Attributes
    ----------
    field_name : str
        Human-readable label (e.g. "PPE Compliance").
    field_value : str
        Current value or status text.
    category : str
        Safety category this field belongs to (e.g. "Hazard", "PPE").
    comment : str
        Optional free-text comment.
    """

    field_name: str
    field_value: str
    category: str
    comment: str = ""


@dataclass
class SafetyTableModel:
    """Typed DTO carrying all data for a safety table.

    Attributes
    ----------
    title : str
        Table heading shown in the first header cell.
    principal : str
        Name of the responsible person shown in a sub-header row.
    categories : List[str]
        All known category values — used for badge colouring.
    fields : List[SafetyFieldModel]
        The data rows to render.
    """

    title: str
    principal: str
    categories: List[str]
    fields: List[SafetyFieldModel] = field(default_factory=list)


# ── constants ───────────────────────────────────────────────────
_COLUMN_HEADERS = ["Field", "Value", "Category", "Comment"]
_N_COLS = len(_COLUMN_HEADERS)
_COL_RATIOS = (0.25, 0.20, 0.20, 0.35)  # must sum to 1.0

_BADGE_FONT = QFont("Segoe UI", 7, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 8)
_SUB_HDR_FONT = QFont("Segoe UI", 8, QFont.Bold)
_SUB_HDR_BG = QColor("#E3F2FD")
_MAX_ROW_H = 26

# Rotating palette for category badges
_BADGE_COLOURS: List[QColor] = [
    ACCENT_BLUE,
    GREEN,
    ORANGE,
    RED,
    NAVY,
    QColor("#7B1FA2"),  # purple
    QColor("#00796B"),  # teal
]


class SafetyTable(BaseTableWidget["SafetyTableModel"]):
    """Read-only safety metrics table for dashboard display.

    Renders safety field data in a four-column grid with category-
    coloured badges.  All data is supplied via :class:`SafetyTableModel`;
    this widget performs no business logic.

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
        self._badge_map: Dict[str, QColor] = {}

    # ── badge colour mapping ────────────────────────────────────
    def _badge_colour(self, category: str) -> QColor:
        """Return a stable colour for *category*, assigning one on first use."""
        if category not in self._badge_map:
            idx = len(self._badge_map) % len(_BADGE_COLOURS)
            self._badge_map[category] = _BADGE_COLOURS[idx]
        return self._badge_map[category]

    # ── column widths ───────────────────────────────────────────
    @staticmethod
    def _col_widths(total_w: float) -> List[float]:
        """Return absolute column widths from the ratio tuple."""
        return [total_w * r for r in _COL_RATIOS]

    # ── rendering ───────────────────────────────────────────────
    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the full safety table inside *inner*.

        Layout
        ------
        * 4 columns at 25/20/20/35 % of total width.
        * Header row + principal sub-header + one row per field.
        * Row height capped at 26 px.
        """
        m = self.model
        n_rows = 1 + len(m.fields)  # header + data
        row_h = min(inner.height() / max(n_rows, 1), _MAX_ROW_H)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        # ── header row ─────────────────────────────────────────
        x = tx
        for idx, hdr in enumerate(_COLUMN_HEADERS):
            self._draw_header_cell(painter, QRectF(x, ty, widths[idx], row_h), hdr)
            x += widths[idx]

        # ── data rows ─────────────────────────────────────────
        for i, fld in enumerate(m.fields):
            ry = ty + (i + 1) * row_h  # +1 for header
            x = tx
            texts = [fld.field_name, fld.field_value, fld.category, fld.comment]

            for col_idx, txt in enumerate(texts):
                cell = QRectF(x, ry, widths[col_idx], row_h)

                if col_idx == 2:
                    # Category column: draw a badge
                    self._draw_data_cell(painter, cell, "", i)
                    self._draw_badge(painter, cell, txt)
                else:
                    align = Qt.AlignLeft if col_idx in (0, 3) else Qt.AlignCenter
                    self._draw_data_cell(
                        painter, cell, txt, i,
                        bold=(col_idx == 0),
                        align=align,
                    )
                x += widths[col_idx]

    # ── badge drawing ───────────────────────────────────────────
    def _draw_badge(self, p: QPainter, cell: QRectF, text: str) -> None:
        """Draw a coloured rounded-rect badge centred in *cell*.

        Parameters
        ----------
        p : QPainter
            Active painter.
        cell : QRectF
            The data cell in which the badge is centred.
        text : str
            Badge label text.
        """
        if not text:
            return
        p.setFont(_BADGE_FONT)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(text) + 12
        th = fm.height() + 4
        bx = cell.center().x() - tw / 2
        by = cell.center().y() - th / 2
        badge_rect = QRectF(bx, by, tw, th)

        colour = self._badge_colour(text)
        p.setBrush(colour)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(badge_rect, 3, 3)

        p.setPen(TEXT_WHITE)
        p.drawText(badge_rect, Qt.AlignCenter, text)
