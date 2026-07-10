"""SQDP bar chart with threshold coloring.

Renders a vertical bar chart where each bar is gradient-filled in
green or red depending on whether its value meets or exceeds the
model's ``target_threshold``.

Rendering behaviour
-------------------
1. **Y gridlines** — drawn from 0 to ``y_max`` in steps of 0.1,
   with text labels at every 0.2.
2. **Threshold line** — horizontal dashed green line at ``target_threshold``.
3. **Bars** — each bar spans 65 % of its slot width and is filled
   with a vertical gradient:

   * ``value >= target_threshold``  →  green gradient (on target)
   * ``value <  target_threshold``  →  red gradient (below target / miss)

4. **X-axis labels** — category names centred below each bar,
   plus a descriptive axis title from the model.
5. **Legend** — two colour swatches (green / red) with their
   meanings, positioned at the top-right of the card.

Input
-----
A :class:`models.chart_models.BarChartModel` dataclass.  The widget
reads it directly and performs no business logic.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QLinearGradient
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.theme import GREEN, RED, HEADER_CLR, GRID_LINE
from models.chart_models import BarChartModel

from .base_chart import BaseChartWidget


class SqdpBarChartWidget(BaseChartWidget[BarChartModel]):
    """Bar chart coloured by binary target threshold (Green vs Red).

    Parameters
    ----------
    model : BarChartModel
        Pre-computed data to render. Can be replaced later via
        :meth:`set_data`.
    parent : QWidget | None
        Optional Qt parent widget.
    """

    def __init__(
        self,
        model: BarChartModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(model, parent)

    # ── BaseChartWidget hooks ───────────────────────────────────

    def get_title(self) -> str:
        """Return the title from the current model."""
        return self.model.title

    def draw_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Render gridlines, threshold, bars, labels, and legend.

        Parameters
        ----------
        painter : QPainter
            Active painter (antialiasing enabled by base class).
        rect : QRectF
            Data area inside the card margins.
        """
        m = self.model
        cx, cy = rect.x(), rect.y()
        cw, ch = rect.width(), rect.height()
        n = len(m.values)
        if n == 0:
            return

        # 1 ─ Y gridlines  (0 → y_max, step 0.2, labels every 0.2)
        self._draw_gridlines(painter, cx, cy, cw, ch, m.y_max, 0.2, 0.2)

        slot_w = cw / n

        # 2 ─ Target threshold dashed line
        th_y = cy + ch - (m.target_threshold / m.y_max) * ch
        painter.setPen(QPen(GRID_LINE, 1, Qt.DashLine))
        painter.drawLine(QPointF(cx, th_y), QPointF(cx + cw, th_y))

        # 3 ─ Coloured bars
        bar_w = slot_w * 0.55
        for i, val in enumerate(m.values):
            bx = cx + i * slot_w + (slot_w - bar_w) / 2
            bh = (val / m.y_max) * ch
            by = cy + ch - bh
            colour = GREEN if val >= m.target_threshold else RED
            painter.setBrush(colour)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 3, 3)

        # 4 ─ X category labels + axis title
        self._draw_x_labels(painter, cx, cy + ch, cw, m.categories, m.x_label)

        # 5 ─ legend
        self._draw_legend(painter, rect)

    # ── private helpers ─────────────────────────────────────────

    def _draw_legend(self, p: QPainter, chart_rect: QRectF) -> None:
        """Draw binary threshold-colour legend swatches at the top of the card."""
        m = self.model
        card_rect = QRectF(4, 4, self.width() - 10, self.height() - 10)
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        bx = 10  # swatch size
        ly = card_rect.y() + 30

        for colour, lbl, dx in [
            (GREEN, f"On Target (>= {m.target_threshold})", card_rect.width() - 210),
            (RED, f"Below Target (< {m.target_threshold})", card_rect.width() - 95),
        ]:
            x = card_rect.x() + dx
            p.setBrush(colour)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(x, ly, bx, bx), 2, 2)
            p.setPen(HEADER_CLR)
            p.drawText(
                QRectF(x + bx + 3, ly - 1, 100, 14),
                Qt.AlignVCenter | Qt.AlignLeft,
                lbl,
            )
