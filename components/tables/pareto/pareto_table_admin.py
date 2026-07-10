"""
components.tables.pareto.pareto_table_admin
===========================================
Pareto Table Admin View (Yellow Concern & Loss Log with Filter Arrows).

Purpose & Similarity to Safety Admin Table
------------------------------------------
Just like `SafetyTableAdmin`, this widget provides an administrative audit
and tracking log styled in the warm golden/yellow palette (#FFF59D headers,
#FBC02D borders, #5D4037 dark brown text) with interactive filter arrows [v].

Define Inputs and Outputs (DTO Level vs Visual Display)
-------------------------------------------------------
At the DTO level (`ParetoLogEntryModel`), we define the full operational context:
* **Inputs (Planned/Target)**: What entered the production cell or planned capacity.
* **Outputs (Actual/Achieved)**: What successfully exited the process.
* **Incident Details**: The `date`, `category`, and root-cause `comment` explaining why Outputs < Inputs.

In the visual table display, to keep the UI clean and focused on root-cause analysis, we display only the 3 primary log columns:
1. **Date (mm/dd)**: Timestamp of the loss incident.
2. **Category**: Pareto loss classification (rendered as a colored badge).
3. **Comment**: Root cause or detailed description of the stoppage.
"""

from __future__ import annotations
from typing import Any, Optional, List
from PyQt5.QtGui import QPainter, QFont, QPen, QColor, QPolygonF
from PyQt5.QtCore import Qt, QRectF, QPointF
from components.tables.base_table import BaseTableWidget
from models.table_models import ParetoLogTableModel
from models.time_context import TimeSpanContext
from components.theme import (
    ADMIN_GOLD_HDR_BG,
    ADMIN_GOLD_BORDER,
    ADMIN_GOLD_TEXT,
    ADMIN_ROW_EVEN,
    ADMIN_ROW_ODD,
    ADMIN_BADGE_PALETTE,
)

_HDR_FONT = QFont("Segoe UI", 8, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 8)
_BADGE_FONT = QFont("Segoe UI", 7, QFont.Bold)


class ParetoTableAdmin(BaseTableWidget[ParetoLogTableModel]):
    """Admin Pareto loss log table with yellow theme, filter arrows, and Date/Category/State/Comment columns."""

    def __init__(self, model: ParetoLogTableModel, parent: Optional[Any] = None) -> None:
        super().__init__(model, parent)
        self._badge_map: dict[str, QColor] = {}

    def on_time_period_changed(self, ctx: TimeSpanContext) -> None:
        """Subscriber Slot: update table title based on active time context."""
        new_model = ParetoLogTableModel(
            title=f"Pareto Loss Log Admin — {ctx.team_scope} ({ctx.window_label})",
            principal=self.model.principal,
            entries=self.model.entries
        )
        self.set_data(new_model)

    def _badge_colour(self, category: str) -> QColor:
        if category not in self._badge_map:
            idx = len(self._badge_map) % len(ADMIN_BADGE_PALETTE)
            self._badge_map[category] = ADMIN_BADGE_PALETTE[idx]
        return self._badge_map[category]

    @staticmethod
    def _col_widths(total_w: float) -> List[float]:
        # 4 columns: Date (15%), Category (22%), State (18%), Comment (45%)
        ratios = (0.15, 0.22, 0.18, 0.45)
        return [total_w * r for r in ratios]

    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the 4-column Pareto admin log table."""
        m = self.model
        if not m.entries:
            return

        n_rows = 1 + len(m.entries)
        row_h = min(inner.height() / max(n_rows, 1), 26.0)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        # ── Header Row (Gold background + Filter Arrows) ──
        x = tx
        headers = ["Date (mm/dd)", "Category", "State", "Comment / Root Cause"]
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
        for i, entry in enumerate(m.entries):
            ry = ty + (i + 1) * row_h
            x = tx
            texts = [entry.date, entry.category, entry.state, entry.comment]

            for col_idx, txt in enumerate(texts):
                cell = QRectF(x, ry, widths[col_idx], row_h)
                row_bg = ADMIN_ROW_EVEN if i % 2 == 0 else ADMIN_ROW_ODD
                
                painter.setBrush(row_bg)
                painter.setPen(QPen(QColor("#FFE082"), 0.8))
                painter.drawRect(cell)

                if col_idx == 1:
                    # Draw Category badge
                    self._draw_badge(painter, cell, txt)
                elif col_idx == 2:
                    # Draw State badge/pill
                    self._draw_state_badge(painter, cell, txt)
                else:
                    painter.setFont(_DATA_FONT)
                    painter.setPen(ADMIN_GOLD_TEXT if col_idx == 0 else QColor("#212121"))
                    align = (Qt.AlignLeft if col_idx in (0, 3) else Qt.AlignCenter) | Qt.AlignVCenter
                    text_rect = cell.adjusted(6, 0, -6, 0) if col_idx in (0, 3) else cell
                    painter.drawText(text_rect, align, txt)
                
                x += widths[col_idx]

    def _draw_badge(self, p: QPainter, cell: QRectF, text: str) -> None:
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

        p.setPen(Qt.white)
        p.drawText(badge_rect, Qt.AlignCenter, text)

    def _draw_state_badge(self, p: QPainter, cell: QRectF, state: str) -> None:
        if not state:
            return
        p.setFont(_BADGE_FONT)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(state) + 14
        th = fm.height() + 4
        bx = cell.center().x() - tw / 2
        by = cell.center().y() - th / 2
        badge_rect = QRectF(bx, by, tw, th)

        # Pick color based on state
        s_lower = state.lower()
        if "open" in s_lower or "pending" in s_lower or "critical" in s_lower:
            colour = QColor("#E53935")  # Red
        elif "progress" in s_lower or "investigat" in s_lower:
            colour = QColor("#1E88E5")  # Blue
        elif "resolv" in s_lower or "clos" in s_lower or "done" in s_lower:
            colour = QColor("#43A047")  # Green
        else:
            colour = QColor("#FB8C00")  # Orange/Amber

        p.setBrush(colour)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(badge_rect, int(th / 2), int(th / 2))  # Pill shape (rounded ends)

        p.setPen(Qt.white)
        p.drawText(badge_rect, Qt.AlignCenter, state)

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
