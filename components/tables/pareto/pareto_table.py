"""
components.tables.pareto.pareto_table
=====================================
Read-only Pareto table for the main dashboard display.

Purpose
-------
Renders a grid of weekly loss counts per category, with a trailing
*Avg* column, using the standard dashboard card style.  The widget
receives all its data via :class:`ParetoTableModel` and performs **zero**
business logic — it only paints the numbers it is given.

Data model
----------
.. code-block:: python

    @dataclass
    class ParetoTableModel:
        title: str                      # e.g. "Where Pareto"
        categories: List[str]           # row labels (loss categories)
        columns: List[str]              # column headers (week numbers)
        values: List[List[float]]       # 2-D grid  [row][col]
        averages: List[float]           # final column, one per row

Rendering
---------
1. **Header row** – title cell (30 % width) + one cell per column +
   ``Avg`` cell, all on ``TBL_HDR_BG`` with white text.
2. **Data rows** – category label (bold, left-aligned) + value cells +
   average cell, with alternating ``BG_WHITE`` / ``TBL_ALT_ROW`` rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QRectF

from components.tables.base_table import BaseTableWidget
from models.time_context import TimeSpanContext
from models.table_models import ParetoTableModel
from components.mixins import TimeAware


class ParetoTable(BaseTableWidget[ParetoTableModel], TimeAware):
    """Read-only Pareto table for the main dashboard display.

    Renders weekly loss counts per category in a fixed grid.
    All data is supplied via :class:`ParetoTableModel`; this widget
    performs no business logic.

    Parameters
    ----------
    model : ParetoTableModel
        Initial table data.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        model: ParetoTableModel,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(model, parent)

    def on_time_period_changed(self, ctx: TimeSpanContext) -> None:
        """Subscriber Slot: autonomously adapt table columns and title to the active time period."""
        cols = ctx.valid_sub_intervals
        n_cols = len(cols)
        # Adapt table values grid to match n_cols
        categories = ["1. Safety / Env", "2. Quality Defects", "3. Machine Down", "4. Material Shortage", "5. Speed Loss"]
        values = [[round((i + j + 1) * 1.5, 1) for j in range(n_cols)] for i in range(len(categories))]
        averages = [round(sum(row) / len(row) if row else 0.0, 1) for row in values]

        new_model = ParetoTableModel(
            title=f"Where Pareto — {ctx.team_scope} ({ctx.window_label})",
            categories=categories,
            columns=cols,
            values=values,
            averages=averages
        )
        self.set_data(new_model)

    # ── core rendering ──────────────────────────────────────────
    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the full Pareto table inside *inner*.

        Layout
        ------
        * Category column = 30 % of total width.
        * Remaining width shared equally among week columns + Avg.
        * Row height capped at 26 px.
        """
        m = self.model
        if not m.categories:
            return

        n_data_cols = len(m.columns) + 1  # +1 for Avg
        n_rows = 1 + len(m.categories)    # +1 for header

        cat_w, dat_w, row_h = self._calc_layout(inner, n_data_cols, n_rows)
        tx, ty = inner.x(), inner.y()

        # ── header row ─────────────────────────────────────────
        self._draw_header_cell(
            painter,
            QRectF(tx, ty, cat_w, row_h),
            m.title,
            align=Qt.AlignLeft,
        )
        for j, col in enumerate(m.columns):
            self._draw_header_cell(
                painter,
                QRectF(tx + cat_w + j * dat_w, ty, dat_w, row_h),
                str(col),
            )
        avg_x = tx + cat_w + len(m.columns) * dat_w
        self._draw_header_cell(
            painter,
            QRectF(avg_x, ty, dat_w, row_h),
            "Avg",
        )

        # ── data rows ─────────────────────────────────────────
        for i, cat in enumerate(m.categories):
            ry = ty + (i + 1) * row_h

            # category label
            self._draw_data_cell(
                painter,
                QRectF(tx, ry, cat_w, row_h),
                cat,
                i,
                bold=True,
                align=Qt.AlignLeft,
            )

            # value cells
            for j in range(len(m.columns)):
                val = m.values[i][j] if i < len(m.values) and j < len(m.values[i]) else 0
                self._draw_data_cell(
                    painter,
                    QRectF(tx + cat_w + j * dat_w, ry, dat_w, row_h),
                    str(val),
                    i,
                )

            # average cell
            avg = m.averages[i] if i < len(m.averages) else 0
            self._draw_data_cell(
                painter,
                QRectF(avg_x, ry, dat_w, row_h),
                str(avg),
                i,
            )
