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

from components.theme import GREEN, RED, HEADER_CLR
from models.chart_models import BarChartModel

from .base_chart import BaseChartWidget


class SqdpBarChartWidget(BaseChartWidget):
    """Bar chart coloured by binary target threshold (Green vs Red).

    Parameters
    ----------
    model : BarChartModel
        Pre-computed data to render.  Can be replaced later via
        :meth:`set_data`.
    parent : QWidget | None
        Optional Qt parent widget.
    """

    def __init__(
        self,
        model: BarChartModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._model: BarChartModel = model

    # ── public API ──────────────────────────────────────────────

    def set_data(self, model: BarChartModel) -> None:
        """Replace the current data model and repaint.

        Parameters
        ----------
        model : BarChartModel
            New data to render.
        """
        self._model = model
        self.update()

    # ── BaseChartWidget hooks ───────────────────────────────────

    def get_title(self) -> str:
        """Return the title from the current model."""
        return self._model.title

    def draw_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Render gridlines, threshold, bars, labels, and legend.

        Parameters
        ----------
        painter : QPainter
            Active painter (antialiasing enabled by base class).
        rect : QRectF
            Data area inside the card margins.
        """
        m = self._model
        cx, cy = rect.x(), rect.y()
        cw, ch = rect.width(), rect.height()
        n = len(m.values)
        if n == 0:
            return

        # 1 ─ Y gridlines  (0 → y_max, step 0.1, labels every 0.2)
        self._draw_gridlines(painter, cx, cy, cw, ch, m.y_max, 0.1, 0.2)

        # 2 ─ target threshold dashed line
        yy = cy + ch - (m.target_threshold / m.y_max) * ch
        painter.setPen(QPen(GREEN, 1.8, Qt.DashLine))
        painter.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))

        # 3 ─ bars with binary gradient fill (Green vs Red)
        bar_area = cw / n
        bar_w = bar_area * 0.65

        for i, v in enumerate(m.values):
            bx = cx + i * bar_area + (bar_area - bar_w) / 2
            bh = (v / m.y_max) * ch
            by = cy + ch - bh
            bar_rect = QRectF(bx, by, bar_w, bh)

            if v >= m.target_threshold:
                colour = GREEN
            else:
                colour = RED

            grad = QLinearGradient(QPointF(bx, by), QPointF(bx, by + bh))
            grad.setColorAt(0, colour.lighter(115))
            grad.setColorAt(1, colour)
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_rect, 2, 2)

        # 4 ─ x-axis category labels
        self._draw_x_labels(painter, cx, cy + ch, cw, m.categories, m.x_label)

        # 5 ─ legend
        self._draw_legend(painter, rect)

    # ── private helpers ─────────────────────────────────────────

    def _draw_legend(self, p: QPainter, chart_rect: QRectF) -> None:
        """Draw binary threshold-colour legend swatches at the top of the card."""
        m = self._model
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
