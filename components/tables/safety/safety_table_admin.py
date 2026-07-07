"""
components.tables.safety.safety_table_admin
===========================================
Safety Table Admin View (Yellow Theme with Filter Arrows).

Purpose
-------
Preserves the detailed safety comment/concern log (the old table structure)
while revamping its aesthetics into the golden/yellow admin palette
requested by the user (matching Image 2).

Visual Features
---------------
* **Yellow/Gold Palette**: Headers rendered in warm gold (#FFF59D / #F0E68C)
  with dark golden brown text (#5D4037) and gold grid borders (#FBC02D).
* **Interactive Filter Arrows**: Every header displays a dropdown/filter
  arrow indicator [v] matching the admin log style.
* **Alternating Warm Rows**: Data rows alternate between white (#FFFFFF)
  and soft cream (#FFFDE7).
"""

from __future__ import annotations
from typing import Any, Optional, List
from PyQt5.QtGui import QPainter, QFont, QPen, QColor, QPolygonF
from PyQt5.QtCore import Qt, QRectF, QPointF
from components.tables.safety.safety_table import SafetyTable, SafetyTableModel
from components.theme import (
    ADMIN_GOLD_HDR_BG,
    ADMIN_GOLD_BORDER,
    ADMIN_GOLD_TEXT,
    ADMIN_ROW_EVEN,
    ADMIN_ROW_ODD,
)

_HDR_FONT = QFont("Segoe UI", 8, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 8)
_BADGE_FONT = QFont("Segoe UI", 7, QFont.Bold)


class SafetyTableAdmin(SafetyTable):
    """Admin view of the safety table in golden/yellow theme with filter arrows."""

    def __init__(self, model: SafetyTableModel, parent: Optional[Any] = None) -> None:
        super().__init__(model, parent)

    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the safety log table using the golden admin theme."""
        m = self.model
        if not m.fields:
            return

        n_rows = 1 + len(m.fields)
        row_h = min(inner.height() / max(n_rows, 1), 26.0)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        # ── Header Row (Gold background + Filter Arrows) ──
        x = tx
        headers = ["Date / Field", "Value", "Category", "Comment / Concern"]
        for idx, hdr in enumerate(headers):
            cell = QRectF(x, ty, widths[idx], row_h)
            
            painter.setBrush(ADMIN_GOLD_HDR_BG)
            painter.setPen(QPen(ADMIN_GOLD_BORDER, 1))
            painter.drawRect(cell)
            
            painter.setFont(_HDR_FONT)
            painter.setPen(ADMIN_GOLD_TEXT)
            text_rect = cell.adjusted(6, 0, -18, 0) if idx in (0, 3) else cell.adjusted(0, 0, -14, 0)
            align = (Qt.AlignLeft if idx in (0, 3) else Qt.AlignCenter) | Qt.AlignVCenter
            painter.drawText(text_rect, align, hdr)
            
            self._draw_filter_arrow(painter, cell)
            x += widths[idx]

        # ── Data Rows ──
        for i, fld in enumerate(m.fields):
            ry = ty + (i + 1) * row_h
            x = tx
            texts = [fld.field_name, fld.field_value, fld.category, fld.comment]

            for col_idx, txt in enumerate(texts):
                cell = QRectF(x, ry, widths[col_idx], row_h)
                row_bg = ADMIN_ROW_EVEN if i % 2 == 0 else ADMIN_ROW_ODD
                
                painter.setBrush(row_bg)
                painter.setPen(QPen(QColor("#FFE082"), 0.8))
                painter.drawRect(cell)

                if col_idx == 2:
                    self._draw_badge(painter, cell, txt)
                else:
                    painter.setFont(_DATA_FONT)
                    painter.setPen(ADMIN_GOLD_TEXT if col_idx == 0 else QColor("#212121"))
                    align = (Qt.AlignLeft if col_idx in (0, 3) else Qt.AlignCenter) | Qt.AlignVCenter
                    text_rect = cell.adjusted(6, 0, -6, 0) if col_idx in (0, 3) else cell
                    painter.drawText(text_rect, align, txt)
                
                x += widths[col_idx]

    @staticmethod
    def _draw_filter_arrow(p: QPainter, cell: QRectF) -> None:
        """Draw a small admin filter arrow [v] in the gold header cell."""
        box_size = 13.0
        margin = 4.0
        bx = cell.right() - box_size - margin
        by = cell.center().y() - box_size / 2.0
        box_rect = QRectF(bx, by, box_size, box_size)
        
        p.setBrush(QColor("#FFFFFF"))
        p.setPen(QPen(ADMIN_GOLD_BORDER, 0.8))
        p.drawRoundedRect(box_rect, 2, 2)
        
        ax = bx + box_size / 2.0
        ay = by + box_size / 2.0 + 1.0
        triangle = QPolygonF([
            QPointF(ax - 2.5, ay - 1.5),
            QPointF(ax + 2.5, ay - 1.5),
            QPointF(ax, ay + 1.5)
        ])
        p.setBrush(ADMIN_GOLD_TEXT)
        p.setPen(Qt.NoPen)
        p.drawPolygon(triangle)
