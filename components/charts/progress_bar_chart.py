"""Progress bar chart — combo bars + two tracking lines.

Renders a chart that combines vertical blue bars (periodic output)
with two overlay lines tracking cumulative progress:

* **Completed** — solid black line with dot markers.
* **Total** — dashed blue line with dot markers.

Rendering behaviour
-------------------
1. **Y gridlines** — drawn from 0 to ``y_max`` in steps of 50,
   with text labels at every 100.
2. **Blue bars** — each bar spans 55 % of its slot width and is
   filled with a vertical gradient from a lighter to a deeper
   ``ACCENT_BLUE``.
3. **Completed line** — solid ``#212121`` (near-black) line of
   width 2 with filled circle markers at each data point.
4. **Total line** — dashed ``ACCENT_BLUE`` line of width 2 with
   filled circle markers at each data point.
5. **X-axis labels** — category names centred below each slot,
   plus a descriptive axis title.
6. **Legend** — two line swatches (solid black + dashed blue)
   positioned at the top-left of the card.

Input
-----
A :class:`models.chart_models.ProgressBarChartModel` dataclass.
The widget reads it directly and performs no business logic.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.theme import ACCENT_BLUE, HEADER_CLR
from models.chart_models import ProgressBarChartModel

from .base_chart import BaseChartWidget


_COMPLETED_CLR = QColor("#212121")


class ProgressBarChartWidget(BaseChartWidget):
    """Combo chart with blue bars and two tracking lines.

    Parameters
    ----------
    model : ProgressBarChartModel
        Pre-computed data to render.  Can be replaced later via
        :meth:`set_data`.
    parent : QWidget | None
        Optional Qt parent widget.
    """

    def __init__(
        self,
        model: ProgressBarChartModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._model: ProgressBarChartModel = model

    # ── public API ──────────────────────────────────────────────

    def set_data(self, model: ProgressBarChartModel) -> None:
        """Replace the current data model and repaint.

        Parameters
        ----------
        model : ProgressBarChartModel
            New data to render.
        """
        self._model = model
        self.update()

    # ── BaseChartWidget hooks ───────────────────────────────────

    def get_title(self) -> str:
        """Return the title from the current model."""
        return self._model.title

    def draw_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Render gridlines, bars, tracking lines, labels, and legend.

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
        n = len(m.categories)
        if n == 0:
            return

        # 1 ─ Y gridlines  (0 → y_max, step 50, labels every 100)
        self._draw_gridlines(painter, cx, cy, cw, ch, m.y_max, 50, 100)

        slot_w = cw / n

        # 2 ─ blue bars
        bar_w = slot_w * 0.55
        for i, v in enumerate(m.bar_values):
            bx = cx + i * slot_w + (slot_w - bar_w) / 2
            bh = (v / m.y_max) * ch
            by = cy + ch - bh
            bar_rect = QRectF(bx, by, bar_w, bh)

            grad = QLinearGradient(QPointF(bx, by), QPointF(bx, by + bh))
            grad.setColorAt(0, ACCENT_BLUE.lighter(140))
            grad.setColorAt(1, ACCENT_BLUE)
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_rect, 1, 1)

        # ── helper: data index → pixel point ──
        def pt(i: int, val: float) -> QPointF:
            x = cx + i * slot_w + slot_w / 2
            y = cy + ch - (val / m.y_max) * ch
            return QPointF(x, y)

        # 3 ─ Completed line (solid black + dots)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(_COMPLETED_CLR, 2.0, Qt.SolidLine))
        for i in range(n - 1):
            painter.drawLine(pt(i, m.line_completed[i]),
                             pt(i + 1, m.line_completed[i + 1]))
        painter.setBrush(_COMPLETED_CLR)
        painter.setPen(QPen(_COMPLETED_CLR, 1))
        for i in range(n):
            painter.drawEllipse(pt(i, m.line_completed[i]), 2.5, 2.5)

        # 4 ─ Total line (dashed blue + dots)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(ACCENT_BLUE, 2.0, Qt.DashLine))
        for i in range(n - 1):
            painter.drawLine(pt(i, m.line_total[i]),
                             pt(i + 1, m.line_total[i + 1]))
        painter.setBrush(ACCENT_BLUE)
        painter.setPen(QPen(ACCENT_BLUE, 1))
        for i in range(n):
            painter.drawEllipse(pt(i, m.line_total[i]), 2.5, 2.5)

        # 5 ─ x-axis category labels
        self._draw_x_labels(painter, cx, cy + ch, cw, m.categories, m.x_label)

        # 6 ─ legend
        self._draw_legend(painter)

    # ── private helpers ─────────────────────────────────────────

    def _draw_legend(self, p: QPainter) -> None:
        """Draw line-style legend swatches at the top of the card."""
        card = QRectF(4, 4, self.width() - 10, self.height() - 10)
        ly = card.y() + 26
        lx = card.x() + 14
        seg = 20  # length of the sample line segment
        p.setFont(QFont("Segoe UI", 7))

        # Completed — solid black line
        p.setPen(QPen(_COMPLETED_CLR, 2, Qt.SolidLine))
        p.drawLine(QPointF(lx, ly + 5), QPointF(lx + seg, ly + 5))
        p.setPen(HEADER_CLR)
        p.drawText(
            QRectF(lx + seg + 4, ly - 2, 90, 14),
            Qt.AlignVCenter | Qt.AlignLeft,
            "Completed",
        )

        # Total — dashed blue line
        off = 120
        p.setPen(QPen(ACCENT_BLUE, 2, Qt.DashLine))
        p.drawLine(QPointF(lx + off, ly + 5), QPointF(lx + off + seg, ly + 5))
        p.setPen(HEADER_CLR)
        p.drawText(
            QRectF(lx + off + seg + 4, ly - 2, 90, 14),
            Qt.AlignVCenter | Qt.AlignLeft,
            "Total",
        )
