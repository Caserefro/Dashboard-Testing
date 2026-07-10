"""Abstract base class for all chart graphic components.

Provides the shared scaffolding that every chart widget needs:

* Inherits :class:`BaseGraphicWidget` to standardize card background drawing,
  model storage (`self.model`), and live `set_data()` updates.
* Renders the chart title centred at the top of the card inner rect.
* Computes a ``chart_rect`` and delegates the actual chart drawing to the abstract
  :meth:`draw_chart` method.
* Exposes reusable helper methods for horizontal gridlines and x-axis category labels.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, TypeVar

from PyQt5.QtGui import QPainter, QFont, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.base import BaseGraphicWidget
from components.theme import (
    HEADER_CLR,
    SUBTEXT,
    GRID_LINE,
)

T = TypeVar("T")


class BaseChartWidget(BaseGraphicWidget[T]):
    """Abstract base for every chart component in the dashboard.

    Class Hierarchy
    ---------------
    ``BaseGraphicContainer`` ← ``BaseGraphicWidget[T]`` ← ``BaseChartWidget[T]`` ← concrete chart
    """

    # Fixed pixel margins around the data area inside the card content rect.
    _MARGINS = {"top": 40, "bot": 36, "left": 40, "right": 12}

    def __init__(self, model: T, parent: Any | None = None) -> None:
        super().__init__(model, parent)

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

    # ── BaseGraphicWidget template method ───────────────────────

    def paint_content(self, painter: QPainter, inner_rect: QRectF) -> None:
        """Render chart title and delegate data rendering to draw_chart()."""
        mg = self._MARGINS
        cx = inner_rect.x() + mg["left"]
        cy = inner_rect.y() + mg["top"]
        cw = inner_rect.width() - mg["left"] - mg["right"]
        ch = inner_rect.height() - mg["top"] - mg["bot"]

        if cw <= 0 or ch <= 0:
            return

        # ── title ──
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(HEADER_CLR)
        painter.drawText(
            QRectF(inner_rect.x(), inner_rect.y(), inner_rect.width(), 20),
            Qt.AlignCenter,
            self.get_title(),
        )

        # ── delegate to subclass ──
        chart_rect = QRectF(cx, cy, cw, ch)
        self.draw_chart(painter, chart_rect)

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
        """Draw horizontal gridlines with optional Y-axis labels."""
        p.setFont(QFont("Segoe UI", 7))
        label_x = cx - self._MARGINS["left"] + 4

        v = 0.0
        while v <= y_max + step * 0.01:  # float tolerance
            yy = cy + ch - (v / y_max) * ch
            p.setPen(QPen(GRID_LINE, 0.5))
            p.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))

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
        """Draw x-axis category tick labels and an axis title."""
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
