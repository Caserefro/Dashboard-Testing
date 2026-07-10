"""
components.charts.safety_bar_chart
==================================
Stacked Safety bar chart with threshold outer edges.

Purpose
-------
Renders a specialized weekly safety bar chart where each bar consists of:
1. **Outer vertical pillars** (left and right edges): Colored **Green** if the
   week's total score meets or exceeds the target threshold (e.g. 2.5), or
   **Red** if it falls below the threshold.
2. **Inner stacked segments**: Four color blocks (Grey, Dark Blue, Amber, Light Blue)
   representing the four safety dimensions (Motivation, Connected, Workload, Teamwork).

This widget performs **zero** business logic and relies completely on
:class:`models.chart_models.SafetyBarChartModel`.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QColor, QPolygonF
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.theme import GREEN, RED, HEADER_CLR
from models.chart_models import SafetyBarChartModel
from .base_chart import BaseChartWidget


_SEGMENT_COLORS = [
    QColor("#757575"),  # Bottom: Grey (Motivation)
    QColor("#1565C0"),  # 2nd: Dark Blue (Connected)
    QColor("#F57C00"),  # 3rd: Amber/Gold (Workload)
    QColor("#29B6F6"),  # Top: Light Blue/Cyan (Teamwork)
]


class SafetyBarChartWidget(BaseChartWidget[SafetyBarChartModel]):
    """Stacked safety bar chart with binary threshold outer edges.

    Parameters
    ----------
    model : SafetyBarChartModel
        Pre-computed stacked safety data to render.
    parent : QWidget | None
        Optional Qt parent widget.
    """

    def __init__(
        self,
        model: SafetyBarChartModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(model, parent)

    def get_title(self) -> str:
        """Return the title from the current model."""
        return self.model.title

    def draw_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Render gridlines, target line, stacked bars with outer pillars, labels, and legend."""
        m = self.model
        cx, cy = rect.x(), rect.y()
        cw, ch = rect.width(), rect.height()
        n = len(m.categories)
        if n == 0:
            return

        # 1 ─ Y gridlines (0 → y_max, step 0.5, labels every 0.5)
        self._draw_gridlines(painter, cx, cy, cw, ch, m.y_max, 0.5, 0.5)

        # 2 ─ Target threshold solid black line with end diamonds
        yy = cy + ch - (m.target_threshold / m.y_max) * ch
        painter.setPen(QPen(QColor("#1E293B"), 2.0))
        painter.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))
        
        # Draw diamond markers at start and end of threshold line
        for dx in [cx, cx + cw]:
            diamond = QPolygonF([
                QPointF(dx, yy - 4),
                QPointF(dx + 4, yy),
                QPointF(dx, yy + 4),
                QPointF(dx - 4, yy),
            ])
            painter.setBrush(QColor("#1E293B"))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(diamond)

        # 3 ─ Bars with outer threshold pillars and inner stacked segments
        bar_area = cw / n
        bar_w = bar_area * 0.68

        for i in range(n):
            bx = cx + i * bar_area + (bar_area - bar_w) / 2
            sub_vals = m.sub_values[i]
            total_val = sum(sub_vals)
            total_bh = (total_val / m.y_max) * ch
            by = cy + ch - total_bh

            # Outer pillars (Green if >= threshold, else Red)
            edge_w = bar_w * 0.18
            colour = GREEN if total_val >= m.target_threshold else RED

            painter.setBrush(colour)
            painter.setPen(Qt.NoPen)
            # Left pillar
            painter.drawRect(QRectF(bx, by, edge_w, total_bh))
            # Right pillar
            painter.drawRect(QRectF(bx + bar_w - edge_w, by, edge_w, total_bh))

            # Inner stacked segments
            inner_bx = bx + edge_w
            inner_w = bar_w - 2 * edge_w
            current_y = cy + ch

            for s, val_s in enumerate(sub_vals):
                if s < len(_SEGMENT_COLORS) and val_s > 0:
                    seg_h = (val_s / m.y_max) * ch
                    seg_y = current_y - seg_h
                    seg_rect = QRectF(inner_bx, seg_y, inner_w, seg_h)
                    
                    painter.setBrush(_SEGMENT_COLORS[s])
                    painter.setPen(QPen(QColor("#FFFFFF"), 0.8))
                    painter.drawRect(seg_rect)
                    current_y = seg_y

        # 4 ─ X-axis category labels
        self._draw_x_labels(painter, cx, cy + ch, cw, m.categories, m.x_label)

        # 5 ─ Legend
        self._draw_legend(painter, rect)

    def _draw_legend(self, p: QPainter, chart_rect: QRectF) -> None:
        """Draw threshold meanings and 4 stacked metric swatches at top right."""
        m = self.model
        card_rect = QRectF(4, 4, self.width() - 10, self.height() - 10)
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        bx = 10  # swatch size
        ly = card_rect.y() + 25

        # Threshold swatches
        swatches = [
            (GREEN, f"On Target (>= {m.target_threshold})"),
            (RED, f"Below Target (< {m.target_threshold})"),
        ]
        
        # Add segment swatches from top to bottom
        for s in reversed(range(min(len(_SEGMENT_COLORS), len(m.legend_labels)))):
            swatches.append((_SEGMENT_COLORS[s], m.legend_labels[s]))

        x_offset = card_rect.width() - 580
        for colour, lbl in swatches:
            x = card_rect.x() + x_offset
            p.setBrush(colour)
            p.setPen(Qt.NoPen)
            p.drawRect(QRectF(x, ly, bx, bx))
            p.setPen(HEADER_CLR)
            p.drawText(
                QRectF(x + bx + 4, ly - 2, 90, 15),
                Qt.AlignVCenter | Qt.AlignLeft,
                lbl,
            )
            x_offset += 95


# Alias for flexible naming
StackedSafetyBarChart = SafetyBarChartWidget
