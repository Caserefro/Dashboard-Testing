"""Approximating Burndown Curve chart graphic component.

Renders an agile burndown chart with historical baseline and smooth delta forecasting:

* **Master Baseline** — dashed grey line (#8D99AE).
* **Live Sprint Actuals** — solid red line (#D90429) with bold dot markers.
* **Slip Track Forecast** — dashed orange line (#F4A261) showing parallel offset.
* **Catch-Up Track Forecast** — solid navy blue line (#1D3557) smoothly tapering to 0.

Rendering behaviour
-------------------
1. **Y gridlines** — drawn from 0 to ``y_max`` in steps of 20, with text labels.
2. **X-axis labels** — category names (e.g. 0%, 20%, ..., 100%) centred across width.
3. **Smooth curves** — drawn across normalized X coordinates (0.0 to 1.0).
4. **Legend** — clean swatch box positioned at the top-right of the card.
5. **Callout Badge** — highlights the Slip Track finish gap (+X pts late).

Input
-----
A :class:`models.chart_models.BurndownChartModel` dataclass.
The widget reads it directly and performs no business logic or curve fitting.
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.theme import HEADER_CLR, SUBTEXT
from models.chart_models import BurndownChartModel
from .base_chart import BaseChartWidget


_MASTER_CLR = QColor("#8D99AE")
_LIVE_CLR = QColor("#D90429")
_SLIP_CLR = QColor("#F4A261")
_CATCHUP_CLR = QColor("#1D3557")


class BurndownChartWidget(BaseChartWidget):
    """Approximating Burndown Curve chart component.

    Parameters
    ----------
    model : BurndownChartModel
        Pre-computed burndown curve data to render. Can be replaced later via
        :meth:`set_data`.
    parent : QWidget | None
        Optional Qt parent widget.
    """

    def __init__(
        self,
        model: BurndownChartModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._model: BurndownChartModel = model

    # ── public API ──────────────────────────────────────────────

    def set_data(self, model: BurndownChartModel) -> None:
        """Replace the current data model and repaint.

        Parameters
        ----------
        model : BurndownChartModel
            New burndown data to render.
        """
        self._model = model
        self.update()

    # ── BaseChartWidget hooks ───────────────────────────────────

    def get_title(self) -> str:
        """Return the title from the current model."""
        return self._model.title

    def draw_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Render gridlines, curves, checkpoints, labels, legend, and callouts.

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

        if not m.x_categories:
            # Render elegant fallback/unsupported notice when Fiscal Weeks is not selected!
            painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
            painter.setPen(QColor("#D90429"))
            painter.drawText(rect.adjusted(0, 40, 0, -40), Qt.AlignCenter, "Sprint Burndown Unavailable")
            painter.setFont(QFont("Segoe UI", 9.5))
            painter.setPen(QColor("#6C757D"))
            painter.drawText(
                rect.adjusted(30, 90, -30, 0),
                Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                f"Sprint Burndown tracking is supported only under 'Fiscal Weeks' (FW) granularity.\n\nCurrently selected: '{m.title.split('—')[-1].strip() if '—' in m.title else 'Days'}'.\nPlease switch to Fiscal Weeks in the top filter bar above to view sprint glide paths and delta metrics."
            )
            return

        # 1 ─ Y gridlines (0 -> y_max, step 20, labels every 20)
        step = max(10.0, m.y_max / 5.0)
        self._draw_gridlines(painter, cx, cy, cw, ch, m.y_max, step, step)

        # 2 ─ X point-based tick labels and vertical gridlines (for continuous line charts!)
        if m.x_categories and len(m.x_categories) > 1:
            painter.setFont(QFont("Segoe UI", 7))
            n_ticks = len(m.x_categories)
            for i, cat in enumerate(m.x_categories):
                x_norm = i / (n_ticks - 1)
                tx = cx + x_norm * cw

                # Subtle vertical gridline at each tick (helps align progress to curve)
                if 0 < i < n_ticks - 1:
                    painter.setPen(QPen(QColor("#E0E0E0"), 1, Qt.DotLine))
                    painter.drawLine(QPointF(tx, cy), QPointF(tx, cy + ch))

                # Tick label centered horizontally around tx
                painter.setPen(HEADER_CLR)
                painter.drawText(QRectF(tx - 30, cy + ch + 4, 60, 14), Qt.AlignCenter, cat)

            # X-axis title
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(SUBTEXT)
            painter.drawText(QRectF(cx, cy + ch + 18, cw, 16), Qt.AlignCenter, m.x_label)

        # Helper: normalized coordinate (x_norm: 0.0-1.0, val: 0.0-y_max) -> pixel QPointF
        def pt(x_norm: float, val: float) -> QPointF:
            px = cx + x_norm * cw
            py = cy + ch - (val / m.y_max) * ch
            return QPointF(px, py)

        # 3 ─ Master Baseline (dashed grey)
        if m.x_smooth and m.line_master and len(m.x_smooth) == len(m.line_master):
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(_MASTER_CLR, 2.0, Qt.DashLine))
            for i in range(len(m.x_smooth) - 1):
                painter.drawLine(pt(m.x_smooth[i], m.line_master[i]),
                                 pt(m.x_smooth[i + 1], m.line_master[i + 1]))

        # 4 ─ Slip Track Forecast (dashed amber)
        if m.x_future and m.line_slip and len(m.x_future) == len(m.line_slip):
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(_SLIP_CLR, 2.5, Qt.DashLine))
            for i in range(len(m.x_future) - 1):
                painter.drawLine(pt(m.x_future[i], m.line_slip[i]),
                                 pt(m.x_future[i + 1], m.line_slip[i + 1]))

        # 5 ─ Catch-Up Track Forecast (solid navy)
        if m.x_future and m.line_catchup and len(m.x_future) == len(m.line_catchup):
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(_CATCHUP_CLR, 3.0, Qt.SolidLine))
            for i in range(len(m.x_future) - 1):
                painter.drawLine(pt(m.x_future[i], m.line_catchup[i]),
                                 pt(m.x_future[i + 1], m.line_catchup[i + 1]))

        # 6 ─ Live Sprint Actuals (solid red + bold dots)
        if m.x_live and m.y_live and len(m.x_live) == len(m.y_live):
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(_LIVE_CLR, 3.0, Qt.SolidLine))
            for i in range(len(m.x_live) - 1):
                painter.drawLine(pt(m.x_live[i], m.y_live[i]),
                                 pt(m.x_live[i + 1], m.y_live[i + 1]))
            painter.setBrush(_LIVE_CLR)
            painter.setPen(QPen(_LIVE_CLR, 1))
            for i in range(len(m.x_live)):
                painter.drawEllipse(pt(m.x_live[i], m.y_live[i]), 4.0, 4.0)

        # 7 ─ Callout badge for Slip Finish at right edge
        if m.deadline_delta > 0 and m.line_slip:
            end_pt = pt(1.0, m.line_slip[-1])
            badge_text = f"+{m.deadline_delta:.1f} pts late"
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(badge_text)
            
            badge_rect = QRectF(end_pt.x() - tw - 12, end_pt.y() - 24, tw + 10, 18)
            painter.setBrush(_SLIP_CLR)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge_rect, 4, 4)
            
            painter.setPen(Qt.white)
            painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

        # 8 ─ Legend (top-right)
        self._draw_legend(painter, cx, cy, cw)

    def _draw_legend(self, p: QPainter, cx: float, cy: float, cw: float) -> None:
        """Render a clean legend box at the top-right of the chart area."""
        legend_w = 210
        legend_h = 76
        lx = cx + cw - legend_w - 4
        ly = cy + 4

        p.setBrush(QColor(255, 255, 255, 230))
        p.setPen(QPen(QColor("#CFD8DC"), 1))
        p.drawRoundedRect(QRectF(lx, ly, legend_w, legend_h), 6, 6)

        p.setFont(QFont("Segoe UI", 8))
        items = [
            ("Master Baseline (Historical)", _MASTER_CLR, Qt.DashLine),
            ("Live Sprint Actuals", _LIVE_CLR, Qt.SolidLine),
            ("Slip Track (+Delta Forecast)", _SLIP_CLR, Qt.DashLine),
            ("Catch-Up Track (Agile Target)", _CATCHUP_CLR, Qt.SolidLine),
        ]

        for i, (label, col, style) in enumerate(items):
            iy = ly + 14 + i * 16
            p.setPen(QPen(col, 2.0, style))
            p.drawLine(QPointF(lx + 8, iy), QPointF(lx + 28, iy))
            if label == "Live Sprint Actuals":
                p.setBrush(col)
                p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(lx + 18, iy), 2.5, 2.5)

            p.setPen(HEADER_CLR)
            p.drawText(QRectF(lx + 34, iy - 7, legend_w - 40, 14), Qt.AlignLeft | Qt.AlignVCenter, label)
