"""
components.sqdp.base_sqdp
==========================
Abstract base widget for all SQDP letter-diagram variants.

This class encapsulates every piece of shared rendering logic for the
Safety-Quality-Delivery-Productivity (SQDP) board.  Concrete subclasses
only need to supply a title and a per-letter label formatter.

Inputs
------
*  A :class:`~models.sqdp_models.SqdpBoardModel` dataclass containing
   one :class:`~models.sqdp_models.SqdpLetterModel` per letter.  The
   model is provided at construction time and can be swapped at runtime
   via :meth:`set_data`.

Rendering
---------
1. ``paint_content()`` divides the inner card area into equal vertical
   sections — one per letter — and delegates each to
   ``_draw_letter()``.
2. ``_draw_letter()`` calculates cell size to fit the available space,
   paints a green/red gradient per cell, overlays the 1-based cell
   number, draws the letter label at the top, and a summary percentage
   at the bottom.
3. ``_draw_legend()`` paints the green/red legend in the bottom-right
   corner of the card.

Subclass contract
-----------------
*  ``get_title() -> str``  – widget display title.
*  ``format_label(letter: SqdpLetterModel) -> str``  – per-letter label
   text rendered above each grid.
"""

from __future__ import annotations

import abc
from typing import Optional

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QLinearGradient
from PyQt5.QtCore import Qt, QRectF, QPointF

from components.base import BaseGraphicWidget
from components.theme import (
    GREEN,
    GREEN_LIGHT,
    RED,
    RED_LIGHT,
    HEADER_CLR,
    TEXT_WHITE,
    SUBTEXT,
    CELL_BORDER,
)
from models.sqdp_models import SqdpBoardModel, SqdpLetterModel


class BaseSqdpWidget(BaseGraphicWidget[SqdpBoardModel]):
    """Abstract base for all SQDP letter-diagram graphic widgets.

    The widget receives a :class:`SqdpBoardModel` and renders every
    letter as a coloured grid.  It performs **zero** business logic —
    all data transformation must happen in the service layer before
    the model reaches this widget.

    Parameters
    ----------
    model : SqdpBoardModel
        The complete SQDP board data to render.
    parent : QWidget, optional
        Qt parent widget.

    Subclass Hooks
    --------------
    get_title()
        Return the widget heading, e.g. ``'SQDP Daily'``.
    format_label(letter)
        Return the text rendered above each letter grid.
    """

    # ── Maximum cell pixel size (prevents oversized grids) ─────
    _MAX_CELL_PX: int = 38

    def __init__(
        self,
        model: SqdpBoardModel,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(model, parent)

    # ── abstract hooks ─────────────────────────────────────────
    @abc.abstractmethod
    def get_title(self) -> str:
        """Return the display title for this SQDP variant."""

    @abc.abstractmethod
    def format_label(self, letter: SqdpLetterModel) -> str:
        """Return the label text rendered above *letter*'s grid."""

    # ── BaseGraphicWidget implementation ───────────────────────
    def paint_content(self, painter: QPainter, inner: QRectF) -> None:
        """Iterate through model letters and paint each grid section.

        Called by :class:`BaseGraphicWidget.paintEvent` after the card
        background has been drawn.  The painter already has antialiasing
        enabled.  This method must **not** call ``painter.end()``.
        """
        letters = self.model.letters
        n = len(letters)
        if n == 0:
            return

        section_width = inner.width() / n
        top_y = inner.y() + 4

        for idx, letter in enumerate(letters):
            centre_x = inner.x() + section_width * idx + section_width / 2
            self._draw_letter(
                painter,
                letter,
                centre_x,
                top_y,
                max_width=section_width * 0.90,
                max_height=inner.height() - 10,
            )

        self._draw_legend(painter, inner)

    # ── core rendering ─────────────────────────────────────────
    def _draw_letter(
        self,
        painter: QPainter,
        letter: SqdpLetterModel,
        centre_x: float,
        y_top: float,
        max_width: float,
        max_height: float,
    ) -> None:
        """Draw one SQDP letter grid with gradient cells and labels.

        Parameters
        ----------
        painter : QPainter
            Active painter (antialiased, card already drawn).
        letter : SqdpLetterModel
            The letter data to render.
        centre_x : float
            Horizontal centre of the section allocated to this letter.
        y_top : float
            Top Y coordinate where the label begins.
        max_width : float
            Maximum pixel width available for the grid.
        max_height : float
            Maximum pixel height available (label + grid + percentage).
        """
        rows = letter.rows
        cols = letter.cols

        # Compute cell size to fit the available space
        cell_size = min(
            max_width / (cols + 0.4),
            (max_height - 50) / (rows + 0.4),
            self._MAX_CELL_PX,
        )
        grid_width = cols * cell_size
        grid_height = rows * cell_size
        grid_x = centre_x - grid_width / 2
        grid_y = y_top + 26

        # ── letter label ──
        label_text = self.format_label(letter)
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(HEADER_CLR)
        painter.drawText(
            QRectF(grid_x - 10, y_top, grid_width + 20, 22),
            Qt.AlignCenter,
            label_text,
        )

        # ── build cell coordinate map ──
        cell_map: dict[tuple[int, int], int] = {
            (r, c): i for i, (r, c) in enumerate(letter.cells)
        }
        number_font = QFont(
            "Segoe UI", max(7, int(cell_size * 0.28)), QFont.Bold,
        )

        # ── paint each cell ──
        for (r, c), idx in cell_map.items():
            rx = grid_x + c * cell_size
            ry = grid_y + r * cell_size
            rect = QRectF(rx + 1, ry + 1, cell_size - 2, cell_size - 2)

            on_target: bool = bool(letter.status[idx])
            base_colour = GREEN if on_target else RED
            light_colour = GREEN_LIGHT if on_target else RED_LIGHT

            gradient = QLinearGradient(
                QPointF(rx, ry), QPointF(rx, ry + cell_size),
            )
            gradient.setColorAt(0, light_colour)
            gradient.setColorAt(1, base_colour)

            painter.setBrush(gradient)
            painter.setPen(QPen(CELL_BORDER, 1.2))
            painter.drawRoundedRect(rect, 2, 2)

            # Cell number (1-based)
            painter.setFont(number_font)
            painter.setPen(TEXT_WHITE)
            painter.drawText(rect, Qt.AlignCenter, str(idx + 1))

        # ── summary percentage ──
        total = len(letter.cells)
        green_count = sum(letter.status)
        pct = int(green_count / total * 100) if total else 0

        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(SUBTEXT)
        painter.drawText(
            QRectF(grid_x - 15, grid_y + grid_height + 3, grid_width + 30, 16),
            Qt.AlignCenter,
            f"{green_count}/{total} ({pct}%)",
        )

    # ── legend ─────────────────────────────────────────────────
    def _draw_legend(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the green/red legend at the bottom-right of the card.

        Parameters
        ----------
        painter : QPainter
            Active painter.
        inner : QRectF
            Inner card rectangle (after padding).
        """
        box_size = 12
        legend_y = inner.bottom() - 16
        legend_x = inner.right() - 230

        painter.setFont(QFont("Segoe UI", 7))

        for colour, label, dx in [
            (GREEN, "On Target", 0),
            (RED, "Needs Attention", 100),
        ]:
            painter.setBrush(colour)
            painter.setPen(QPen(CELL_BORDER, 0.8))
            painter.drawRoundedRect(
                QRectF(legend_x + dx, legend_y, box_size, box_size), 2, 2,
            )
            painter.setPen(HEADER_CLR)
            painter.drawText(
                QRectF(legend_x + dx + box_size + 4, legend_y - 1, 90, 16),
                Qt.AlignVCenter | Qt.AlignLeft,
                label,
            )
