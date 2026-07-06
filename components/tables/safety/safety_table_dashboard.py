"""
components.tables.safety.safety_table_dashboard
===============================================
Revamped Safety Table for Dashboard Display (Summary Metric Table).

Purpose
-------
Renders the high-level weekly/sprint psychological safety summary matrix
(e.g., Week 5 across top, columns for # No responses, Motivation Average,
Connection Average, Workload Average, Teamwork Average, and Total Average).

Visual Features
---------------
* **Top Spanning Header**: Gray background (#CFD8DC) with centered period text.
* **Column Headers**: 
  - Standard columns use light steel blue (#BBDEFB).
  - Total Average column uses orange (#F57C00) with bold white text.
  - Every header displays an interactive filter / dropdown arrow indicator [v].
* **Data Row**:
  - Total Average cell is dynamically highlighted green (#A5D6A7) if meeting
    or exceeding threshold, otherwise soft red (#FFCDD2).
"""

from __future__ import annotations
from typing import Any, Optional, List
from PyQt5.QtGui import QPainter, QFont, QPen, QColor, QPolygonF
from PyQt5.QtCore import Qt, QRectF, QPointF
from components.theme import GRID_LINE, HEADER_CLR, TEXT_WHITE, BG_WHITE
from components.tables.base_table import BaseTableWidget
from models.table_models import SafetySummaryTableModel

_HDR_FONT = QFont("Segoe UI", 9, QFont.Bold)
_TOP_HDR_FONT = QFont("Segoe UI", 10, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 9)

_TOP_HDR_BG = QColor("#CFD8DC")
_COL_HDR_BG = QColor("#BBDEFB")
_TOTAL_HDR_BG = QColor("#F57C00")
_TOTAL_GOOD_BG = QColor("#A5D6A7")
_TOTAL_BAD_BG = QColor("#FFCDD2")


class SafetyTableDashboard(BaseTableWidget[SafetySummaryTableModel]):
    """Revamped dashboard summary table for safety metrics (e.g. Week 5 averages)."""

    def __init__(self, model: SafetySummaryTableModel, parent: Optional[Any] = None) -> None:
        super().__init__(model, parent)

    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the 3-row summary dashboard table."""
        m = self.model
        if not m.headers or not m.values:
            return

        n_cols = len(m.headers)
        row_h = min(inner.height() / 3.0, 32.0)
        col_w = inner.width() / max(n_cols, 1)
        tx, ty = inner.x(), inner.y()

        # ── Row 0: Top Spanning Period Header (e.g., Week 5) ──
        top_rect = QRectF(tx, ty, inner.width(), row_h)
        painter.setBrush(_TOP_HDR_BG)
        painter.setPen(QPen(GRID_LINE, 1))
        painter.drawRect(top_rect)
        painter.setFont(_TOP_HDR_FONT)
        painter.setPen(HEADER_CLR)
        painter.drawText(top_rect, Qt.AlignCenter, m.period_title)

        # ── Row 1: Column Headers with Filter Arrows ──
        for j, hdr in enumerate(m.headers):
            cell = QRectF(tx + j * col_w, ty + row_h, col_w, row_h)
            is_total = (j == m.total_index)
            bg = _TOTAL_HDR_BG if is_total else _COL_HDR_BG
            
            painter.setBrush(bg)
            painter.setPen(QPen(GRID_LINE, 1))
            painter.drawRect(cell)
            
            painter.setFont(_HDR_FONT)
            painter.setPen(TEXT_WHITE if is_total else HEADER_CLR)
            
            # Leave space on right for filter arrow
            text_rect = cell.adjusted(4, 0, -18, 0)
            painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, hdr)
            
            # Draw filter arrow [v]
            self._draw_filter_arrow(painter, cell, is_total)

        # ── Row 2: Data Values ──
        for j, val in enumerate(m.values):
            cell = QRectF(tx + j * col_w, ty + 2 * row_h, col_w, row_h)
            is_total = (j == m.total_index)
            
            if is_total:
                try:
                    num_val = float(val)
                    bg = _TOTAL_GOOD_BG if num_val >= m.target_threshold else _TOTAL_BAD_BG
                except ValueError:
                    bg = _TOTAL_GOOD_BG
            else:
                bg = BG_WHITE
                
            painter.setBrush(bg)
            painter.setPen(QPen(GRID_LINE, 1))
            painter.drawRect(cell)
            
            painter.setFont(_DATA_FONT)
            painter.setPen(HEADER_CLR)
            painter.drawText(cell, Qt.AlignCenter | Qt.AlignVCenter, val)

    @staticmethod
    def _draw_filter_arrow(p: QPainter, cell: QRectF, is_total: bool) -> None:
        """Draw a small dropdown/filter arrow box in the header cell."""
        box_size = 14.0
        margin = 4.0
        bx = cell.right() - box_size - margin
        by = cell.center().y() - box_size / 2.0
        box_rect = QRectF(bx, by, box_size, box_size)
        
        # White/light box for filter button
        p.setBrush(QColor("#FFFFFF") if not is_total else QColor("#FFE0B2"))
        p.setPen(QPen(GRID_LINE, 0.8))
        p.drawRoundedRect(box_rect, 2, 2)
        
        # Down triangle arrow
        ax = bx + box_size / 2.0
        ay = by + box_size / 2.0 + 1.0
        triangle = QPolygonF([
            QPointF(ax - 3.0, ay - 2.0),
            QPointF(ax + 3.0, ay - 2.0),
            QPointF(ax, ay + 2.0)
        ])
        p.setBrush(HEADER_CLR if not is_total else QColor("#D84315"))
        p.setPen(Qt.NoPen)
        p.drawPolygon(triangle)
