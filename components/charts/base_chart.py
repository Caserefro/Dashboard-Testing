"""Abstract base class for all chart graphic components.

Provides the shared scaffolding that every chart widget needs:

* Draws a white card background with a faint drop-shadow.
* Renders the chart title centred at the top of the card.
* Computes a ``chart_rect`` (the region inside fixed margins)
  and delegates the actual chart drawing to the abstract
  :meth:`draw_chart` method.
* Exposes reusable helper methods for horizontal gridlines
  and x-axis category labels so that subclasses stay DRY.

Subclass contract
-----------------
Concrete subclasses must implement:

* ``get_title() -> str``
      Return the title text rendered at the top of the card.
* ``draw_chart(painter, rect) -> None``
      Render all data-specific visuals (bars, lines, legend, etc.)
      inside the given *rect*.

Rendering notes
---------------
* Fonts: **Segoe UI** at various point sizes, consistent with the
  rest of the dashboard.
* Margins are ``{top: 50, bot: 40, left: 44, right: 16}`` — wide
  enough for Y-axis labels on the left and breathing room on the
  right.
* ``painter.end()`` is **always** called before ``paintEvent``
  returns, even on early-exit paths.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.theme import (
    HEADER_CLR,
    SUBTEXT,
    GRID_LINE,
    paint_card,
)


# Resolve metaclass conflict: QWidget uses sip.wrappertype while
# ABC uses ABCMeta.  A combined metaclass satisfies both.
_QABCMeta = type("_QABCMeta", (type(QWidget), ABCMeta), {})


class BaseChartWidget(QWidget, metaclass=_QABCMeta):
    """Abstract base for every chart component in the dashboard.

    Parameters
    ----------
    parent : QWidget | None
        Optional parent widget (standard Qt ownership model).

    Class Hierarchy
    ---------------
    ``QWidget`` ← ``BaseChartWidget`` ← concrete chart
    (e.g. ``SqdpBarChartWidget``, ``ProgressBarChartWidget``).
    """

    # Fixed pixel margins around the data area inside the card.
    _MARGINS = {"top": 50, "bot": 40, "left": 44, "right": 16}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    # ── abstract hooks ──────────────────────────────────────────

    @abstractmethod
    def get_title(self) -> str:
        """Return the title text to render above the chart."""

    @abstractmethod
    def draw_chart(self, painter: QPainter, rect: QRectF) -> None:
        """Draw all data-specific visuals inside *rect*.

        Parameters
        ----------
        painter : QPainter
            Active painter with antialiasing already enabled.
        rect : QRectF
            The rectangular region inside the card margins where
            gridlines, bars, lines, and labels should be drawn.
        """

    # ── paintEvent (template method) ────────────────────────────

    def paintEvent(self, event: Any) -> None:  # noqa: N802
        """Card → title → chart_rect → draw_chart → end."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        mg = self._MARGINS
        cx = card.x() + mg["left"]
        cy = card.y() + mg["top"]
        cw = card.width() - mg["left"] - mg["right"]
        ch = card.height() - mg["top"] - mg["bot"]

        if cw <= 0 or ch <= 0:
            p.end()
            return

        # ── title ──
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(HEADER_CLR)
        p.drawText(
            QRectF(card.x(), card.y() + 8, card.width(), 20),
            Qt.AlignCenter,
            self.get_title(),
        )

        # ── delegate to subclass ──
        chart_rect = QRectF(cx, cy, cw, ch)
        self.draw_chart(p, chart_rect)

        p.end()

    # ── shared helpers ──────────────────────────────────────────

    def _draw_gridlines(
        self,
        p: QPainter,
        cx: float,
        cy: float,
        cw: float,
        ch: float,
        y_max: float,
        step: float,
        label_every: float,
    ) -> None:
        """Draw horizontal gridlines with optional Y-axis labels.

        Parameters
        ----------
        p : QPainter
            Active painter.
        cx, cy, cw, ch : float
            Chart-area origin and dimensions.
        y_max : float
            Maximum value on the Y axis.
        step : float
            Distance between consecutive gridlines in data units.
        label_every : float
            Only gridlines whose data value is a multiple of this
            number receive a text label on the left.
        """
        p.setFont(QFont("Segoe UI", 7))
        # The left edge of the card (for label positioning).
        label_x = cx - self._MARGINS["left"] + 4

        v = 0.0
        while v <= y_max + step * 0.01:  # float tolerance
            yy = cy + ch - (v / y_max) * ch
            p.setPen(QPen(GRID_LINE, 0.5))
            p.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))

            # Label check — use a small epsilon for float comparison.
            remainder = v % label_every if label_every else 1.0
            if remainder < step * 0.01 or abs(remainder - label_every) < step * 0.01:
                p.setPen(SUBTEXT)
                label_text = f"{v:.1f}" if y_max <= 10 else str(int(v))
                p.drawText(
                    QRectF(label_x, yy - 7, self._MARGINS["left"] - 8, 14),
                    Qt.AlignRight | Qt.AlignVCenter,
                    label_text,
                )
            v += step

    def _draw_x_labels(
        self,
        p: QPainter,
        cx: float,
        cy_bottom: float,
        cw: float,
        categories: list[str],
        x_label: str,
    ) -> None:
        """Draw x-axis category tick labels and an axis title.

        Parameters
        ----------
        p : QPainter
            Active painter.
        cx : float
            Left edge of the chart data area.
        cy_bottom : float
            Y-coordinate of the bottom edge of the chart data area.
        cw : float
            Width of the chart data area.
        categories : list[str]
            Per-bar / per-point category labels.
        x_label : str
            Descriptive axis title drawn below the tick labels.
        """
        n = len(categories)
        if n == 0:
            return

        slot_w = cw / n

        p.setFont(QFont("Segoe UI", 7))
        p.setPen(HEADER_CLR)
        for i, cat in enumerate(categories):
            lx = cx + i * slot_w
            p.drawText(
                QRectF(lx, cy_bottom + 3, slot_w, 14),
                Qt.AlignCenter,
                str(cat),
            )

        p.setFont(QFont("Segoe UI", 8))
        p.setPen(SUBTEXT)
        p.drawText(
            QRectF(cx, cy_bottom + 18, cw, 16),
            Qt.AlignCenter,
            x_label,
        )
