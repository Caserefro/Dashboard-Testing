"""
components.tables.pareto.pareto_category_table
==============================================
Pareto Category Reading & Reference Table (2-Column View).

Purpose
-------
Renders a clean 2-column reference table for reading Pareto loss categories
and their corresponding descriptions.
* Column 1: Category Name (rendered as a distinct colored badge or bold text).
* Column 2: Description (detailed explanation of what falls under the category).

This widget receives all its data via :class:`ParetoCategoryTableModel` and
performs **zero** business logic — it only paints the table.
"""

from __future__ import annotations
from typing import Any, Optional, List
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF
from components.tables.base_table import BaseTableWidget
from models.table_models import ParetoCategoryTableModel

# ==============================================================================
# COLOR CONFIGURATION
# Modify these constants directly in the code to customize the table appearance.
# ==============================================================================
HEADER_BG_COLOR = QColor("#FFF59D")    # Warm yellow/gold header background
HEADER_TEXT_COLOR = QColor("#5D4037")  # Dark brown header text
BORDER_COLOR = QColor("#FBC02D")       # Golden yellow border color
ROW_EVEN_BG = QColor("#FFFFFF")        # Pure white even rows
ROW_ODD_BG = QColor("#FFFDE7")         # Soft warm yellow tint for odd rows
DESC_TEXT_COLOR = QColor("#212121")    # Main dark text color for descriptions
BADGE_TEXT_COLOR = QColor("#FFFFFF")   # White text inside category badges

# Palette of badge colors assigned sequentially to each category
CATEGORY_BADGE_PALETTE = [
    QColor("#E53935"),  # Red
    QColor("#FB8C00"),  # Orange
    QColor("#1E88E5"),  # Blue
    QColor("#43A047"),  # Green
    QColor("#8E24AA"),  # Purple
    QColor("#00ACC1"),  # Cyan
]
# ==============================================================================

_HDR_FONT = QFont("Segoe UI", 9, QFont.Bold)
_DESC_FONT = QFont("Segoe UI", 8)
_BADGE_FONT = QFont("Segoe UI", 8, QFont.Bold)


class ParetoCategoryTable(BaseTableWidget[ParetoCategoryTableModel]):
    """Pareto category reading table with 2 columns (Category & Description) and accessible color config."""

    def __init__(self, model: ParetoCategoryTableModel, parent: Optional[Any] = None) -> None:
        super().__init__(model, parent)
        self._badge_map: dict[str, QColor] = {}

    def _badge_colour(self, category: str) -> QColor:
        if category not in self._badge_map:
            idx = len(self._badge_map) % len(CATEGORY_BADGE_PALETTE)
            self._badge_map[category] = CATEGORY_BADGE_PALETTE[idx]
        return self._badge_map[category]

    @staticmethod
    def _col_widths(total_w: float) -> List[float]:
        # 2 columns: Category (28%), Description (72%)
        ratios = (0.28, 0.72)
        return [total_w * r for r in ratios]

    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the 2-column Pareto category reference table."""
        m = self.model
        if not m.entries:
            return

        n_rows = 1 + len(m.entries)
        row_h = min(inner.height() / max(n_rows, 1), 32.0)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        # ── Header Row ──
        x = tx
        headers = ["Category", "Description / Definition"]
        for idx, hdr in enumerate(headers):
            cell = QRectF(x, ty, widths[idx], row_h)
            
            painter.setBrush(HEADER_BG_COLOR)
            painter.setPen(QPen(BORDER_COLOR, 1))
            painter.drawRect(cell)
            
            painter.setFont(_HDR_FONT)
            painter.setPen(HEADER_TEXT_COLOR)
            text_rect = cell.adjusted(10, 0, -10, 0)
            align = Qt.AlignLeft | Qt.AlignVCenter if idx == 1 else Qt.AlignCenter
            painter.drawText(text_rect, align, hdr)
            x += widths[idx]

        # ── Data Rows ──
        for i, entry in enumerate(m.entries):
            ry = ty + (i + 1) * row_h
            x = tx

            # Background alternating color
            row_bg = ROW_EVEN_BG if i % 2 == 0 else ROW_ODD_BG

            # Column 0: Category Badge
            cell_cat = QRectF(x, ry, widths[0], row_h)
            painter.setBrush(row_bg)
            painter.setPen(QPen(BORDER_COLOR, 0.5))
            painter.drawRect(cell_cat)

            badge_bg = self._badge_colour(entry.category)
            bw = min(cell_cat.width() - 16, 140)
            bh = min(row_h - 8, 20)
            bx = cell_cat.x() + (cell_cat.width() - bw) / 2
            by = cell_cat.y() + (cell_cat.height() - bh) / 2
            badge = QRectF(bx, by, bw, bh)

            painter.setBrush(badge_bg)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge, 4, 4)

            painter.setFont(_BADGE_FONT)
            painter.setPen(BADGE_TEXT_COLOR)
            painter.drawText(badge, Qt.AlignCenter, entry.category)

            # Column 1: Description Text
            x += widths[0]
            cell_desc = QRectF(x, ry, widths[1], row_h)
            painter.setBrush(row_bg)
            painter.setPen(QPen(BORDER_COLOR, 0.5))
            painter.drawRect(cell_desc)

            painter.setFont(_DESC_FONT)
            painter.setPen(DESC_TEXT_COLOR)
            desc_rect = cell_desc.adjusted(10, 0, -10, 0)
            painter.drawText(desc_rect, Qt.AlignLeft | Qt.AlignVCenter, entry.description)
