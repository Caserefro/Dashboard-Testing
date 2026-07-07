"""
components.tables.pareto.pareto_table_create
============================================
Pareto Table Create (Loss Log without State column, filled by text).

Purpose
-------
Renders the creation / logging view for Pareto loss tracking. Exactly like
`ParetoTableAdmin`, but without the State column (since new logs start without
a resolved state), and all columns (including Category) are displayed as pure text
rather than colored badges.

Columns:
1. Date (mm/dd)
2. Category (text)
3. Comment / Root Cause (text)

This widget receives all its data via :class:`ParetoLogCreateTableModel` and
performs **zero** business logic.
"""

from __future__ import annotations
from typing import Any, Optional, List
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF
from components.tables.base_table import BaseTableWidget
from models.table_models import ParetoLogCreateTableModel

# ==============================================================================
# COLOR CONFIGURATION
# Modify these constants directly in the code to customize the table appearance.
# ==============================================================================
HEADER_BG_COLOR = QColor("#FFF59D")    # Warm yellow/gold header background
HEADER_TEXT_COLOR = QColor("#5D4037")  # Dark brown header text
BORDER_COLOR = QColor("#FBC02D")       # Golden yellow border color
ROW_EVEN_BG = QColor("#FFFFFF")        # Pure white even rows
ROW_ODD_BG = QColor("#FFFDE7")         # Soft warm yellow tint for odd rows
TEXT_COLOR = QColor("#212121")         # Main dark text color for all cells
DATE_TEXT_COLOR = QColor("#5D4037")    # Slightly darker/emphasized color for dates
# ==============================================================================

_HDR_FONT = QFont("Segoe UI", 8, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 8)
_DATE_FONT = QFont("Segoe UI", 8, QFont.Bold)


class ParetoTableCreate(BaseTableWidget[ParetoLogCreateTableModel]):
    """Pareto loss creation table (no State col, all text cells) with accessible color config."""

    def __init__(self, model: ParetoLogCreateTableModel, parent: Optional[Any] = None) -> None:
        super().__init__(model, parent)

    @staticmethod
    def _col_widths(total_w: float) -> List[float]:
        # 3 columns: Date (16%), Category (28%), Comment / Root Cause (56%)
        ratios = (0.16, 0.28, 0.56)
        return [total_w * r for r in ratios]

    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the 3-column Pareto creation text table."""
        m = self.model
        if not m.entries:
            return

        n_rows = 1 + len(m.entries)
        row_h = min(inner.height() / max(n_rows, 1), 26.0)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        # ── Header Row ──
        x = tx
        headers = ["Date (mm/dd)", "Category", "Comment / Root Cause"]
        for idx, hdr in enumerate(headers):
            cell = QRectF(x, ty, widths[idx], row_h)
            
            painter.setBrush(HEADER_BG_COLOR)
            painter.setPen(QPen(BORDER_COLOR, 1))
            painter.drawRect(cell)
            
            painter.setFont(_HDR_FONT)
            painter.setPen(HEADER_TEXT_COLOR)
            text_rect = cell.adjusted(8, 0, -8, 0)
            align = Qt.AlignLeft | Qt.AlignVCenter
            painter.drawText(text_rect, align, hdr)
            x += widths[idx]

        # ── Data Rows (All Text) ──
        for i, entry in enumerate(m.entries):
            ry = ty + (i + 1) * row_h
            x = tx
            texts = [entry.date, entry.category, entry.comment]

            row_bg = ROW_EVEN_BG if i % 2 == 0 else ROW_ODD_BG

            for col_idx, txt in enumerate(texts):
                cell = QRectF(x, ry, widths[col_idx], row_h)
                
                painter.setBrush(row_bg)
                painter.setPen(QPen(BORDER_COLOR, 0.5))
                painter.drawRect(cell)

                # Style text cell
                font = _DATE_FONT if col_idx == 0 else _DATA_FONT
                color = DATE_TEXT_COLOR if col_idx == 0 else TEXT_COLOR

                painter.setFont(font)
                painter.setPen(color)
                text_rect = cell.adjusted(8, 0, -8, 0)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, txt)

                x += widths[col_idx]
