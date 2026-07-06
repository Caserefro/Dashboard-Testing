"""
components.tables.guide_table
=============================
Pure text matrix reference guide table for dashboard display.

Purpose
-------
Renders a pure text matrix guide (such as a Psychological Safety Metric
guide or Pareto loss classification matrix). Displays a spanning header title across
the data columns, a left-hand row label column, colored column headers (e.g. 1, 2, 3, 4),
and word-wrapped text data cells.

This widget performs **zero** business logic and relies completely on
:class:`TextGuideTableModel`.

Aliases
-------
* ``TextGuideTable``
* ``SafetyGuideTable``
* ``ParetoTableGuide``
"""

from __future__ import annotations

from typing import Any, Optional
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

from components.theme import (
    HEADER_CLR,
    TEXT_WHITE,
    BG_WHITE,
    GRID_LINE,
    TBL_ALT_ROW,
)
from components.tables.base_table import BaseTableWidget
from models.table_models import TextGuideTableModel


_TITLE_BG = QColor("#E3F2FD")
_TITLE_BORDER = QColor("#0D47A1")
_TITLE_FONT = QFont("Segoe UI", 9, QFont.Bold)
_HDR_FONT = QFont("Segoe UI", 11, QFont.Bold)
_ROW_LABEL_FONT = QFont("Segoe UI", 9, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 9)


class TextGuideTable(BaseTableWidget[TextGuideTableModel]):
    """Pure text matrix reference guide table for dashboard display.

    Renders a multi-row, multi-column text reference table with colored
    column headers and word-wrapped text cells.

    Parameters
    ----------
    model : TextGuideTableModel
        The table data model containing title, headers, labels, and text matrix.
    parent : QWidget, optional
        Parent widget in the Qt object tree.
    """

    def __init__(
        self,
        model: TextGuideTableModel,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(model, parent)

    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the text guide table inside *inner*.

        Layout
        ------
        * Col 0 (Row Labels): ~18% of width.
        * Cols 1..N (Data): Equal division of remaining ~82% width.
        * Row 0: Spanning title across Cols 1..N.
        * Row 1: Colored column headers (1, 2, 3, 4).
        * Rows 2..N+1: Row label + word-wrapped text data cells.
        """
        m = self.model
        n_cols = len(m.columns)
        n_rows = 2 + len(m.row_labels)
        
        # Allow vertical expansion up to 52px per row for multi-word text cells
        row_h = min(inner.height() / max(n_rows, 1), 52.0)
        
        cat_w = inner.width() * 0.18
        data_w = (inner.width() - cat_w) / max(n_cols, 1)
        tx, ty = inner.x(), inner.y()

        # ── Row 0: Title Spanning across Cols 1..N ──
        if m.row_label_header:
            hdr0_rect = QRectF(tx, ty, cat_w, row_h)
            painter.setBrush(BG_WHITE)
            painter.setPen(QPen(GRID_LINE, 1))
            painter.drawRect(hdr0_rect)
            painter.setFont(_ROW_LABEL_FONT)
            painter.setPen(HEADER_CLR)
            painter.drawText(hdr0_rect, Qt.AlignCenter, m.row_label_header)

        title_rect = QRectF(tx + cat_w, ty, inner.width() - cat_w, row_h)
        painter.setBrush(_TITLE_BG)
        painter.setPen(QPen(_TITLE_BORDER, 1))
        painter.drawRect(title_rect)
        painter.setFont(_TITLE_FONT)
        painter.setPen(_TITLE_BORDER)
        painter.drawText(title_rect, Qt.AlignCenter, m.title.upper())

        # ── Row 1: Colored Column Headers ──
        empty_lbl_rect = QRectF(tx, ty + row_h, cat_w, row_h)
        painter.setBrush(BG_WHITE)
        painter.setPen(QPen(GRID_LINE, 1))
        painter.drawRect(empty_lbl_rect)

        for j, col_model in enumerate(m.columns):
            col_rect = QRectF(tx + cat_w + j * data_w, ty + row_h, data_w, row_h)
            col_bg = QColor(col_model.color)
            painter.setBrush(col_bg)
            painter.setPen(QPen(QColor("#FFFFFF"), 1.2))
            painter.drawRect(col_rect)
            painter.setFont(_HDR_FONT)
            painter.setPen(TEXT_WHITE)
            painter.drawText(col_rect, Qt.AlignCenter, col_model.header)

        # ── Rows 2..N+1: Data Rows ──
        for r, label in enumerate(m.row_labels):
            ry = ty + (r + 2) * row_h
            row_bg = BG_WHITE if r % 2 == 0 else TBL_ALT_ROW

            # Row label cell (Col 0)
            label_rect = QRectF(tx, ry, cat_w, row_h)
            painter.setBrush(row_bg)
            painter.setPen(QPen(GRID_LINE, 0.8))
            painter.drawRect(label_rect)
            painter.setFont(_ROW_LABEL_FONT)
            painter.setPen(HEADER_CLR)
            painter.drawText(
                label_rect.adjusted(10, 0, -4, 0),
                Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap,
                label,
            )

            # Data cells (Cols 1..N)
            for c in range(n_cols):
                cell_rect = QRectF(tx + cat_w + c * data_w, ry, data_w, row_h)
                painter.setBrush(row_bg)
                painter.setPen(QPen(GRID_LINE, 0.8))
                painter.drawRect(cell_rect)
                painter.setFont(_DATA_FONT)
                painter.setPen(QColor("#1E293B"))
                text_val = m.matrix[r][c] if r < len(m.matrix) and c < len(m.matrix[r]) else ""
                painter.drawText(
                    cell_rect.adjusted(6, 4, -6, -4),
                    Qt.AlignCenter | Qt.TextWordWrap,
                    text_val,
                )


# Aliases for flexible naming across the dashboard
SafetyGuideTable = TextGuideTable
ParetoTableGuide = TextGuideTable
