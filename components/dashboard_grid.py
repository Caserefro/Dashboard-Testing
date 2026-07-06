"""Scrollable Dashboard Grid container component.

Provides a scrollable, grid-based dashboard container where any number of
SOLID graphic widgets (SQDP boards, charts, tables, selection bars) can be
arranged in a multi-column, multi-row layout.

SOLID & No-Code Architecture
----------------------------
This container is designed so that layouts can be defined declaratively in code
now (via :class:`GridItemConfig` or direct calls to :meth:`add_widget`), and later
populated seamlessly from no-code JSON/YAML config files or a visual drag-and-drop
dashboard builder without modifying any rendering or widget logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget,
    QScrollArea,
    QGridLayout,
    QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt


@dataclass
class GridItemConfig:
    """Declarative configuration for placing a widget in the dashboard grid.

    Attributes:
        widget: The instantiated graphic or control widget.
        row: Grid row index (0-indexed).
        col: Grid column index (0-indexed).
        row_span: Number of rows this widget spans (default 1).
        col_span: Number of columns this widget spans (default 1).
        min_height: Minimum pixel height to enforce for proper vertical scrolling
                    and visual balance (default None).
    """

    widget: QWidget
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    min_height: Optional[int] = None


class ScrollableDashboardGrid(QScrollArea):
    """A scrollable, grid-based dashboard container.

    Parameters
    ----------
    parent : QWidget | None
        Optional parent widget.
    columns : int
        Number of equal-width columns in the grid (default 2).
    spacing : int
        Pixel spacing between grid cells (default 16).
    margins : int
        Outer pixel margins around the grid (default 12).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        columns: int = 2,
        spacing: int = 16,
        margins: int = 12,
    ) -> None:
        super().__init__(parent)
        self.columns = columns
        self.spacing = spacing
        self.margins = margins

        # 1 ── Configure QScrollArea properties for responsive resizing
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QWidget#DashboardGridContainer { background: transparent; }"
        )

        # 2 ── Create internal container and QGridLayout
        self.container = QWidget()
        self.container.setObjectName("DashboardGridContainer")
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(margins, margins, margins, margins)
        self.grid_layout.setSpacing(spacing)

        # Ensure columns have equal stretch factor so side-by-side charts match width
        for c in range(columns):
            self.grid_layout.setColumnStretch(c, 1)

        self.setWidget(self.container)
        self._items: List[GridItemConfig] = []

    # ── Public API ──────────────────────────────────────────────

    def add_widget(
        self,
        widget: QWidget,
        row: int,
        col: int,
        row_span: int = 1,
        col_span: int = 1,
        min_height: Optional[int] = None,
    ) -> None:
        """Add a graphic component to the grid at the specified coordinates.

        Parameters
        ----------
        widget : QWidget
            The graphic component (chart, table, SQDP board, selection bar).
        row, col : int
            Grid coordinates (0-indexed).
        row_span, col_span : int
            Number of rows/columns to span.
        min_height : int | None
            Optional minimum pixel height to enforce for vertical scrolling.
        """
        config = GridItemConfig(
            widget=widget,
            row=row,
            col=col,
            row_span=row_span,
            col_span=col_span,
            min_height=min_height,
        )
        self._items.append(config)
        self._apply_item(config)

    def setup_from_config(self, configs: List[GridItemConfig]) -> None:
        """Populate the entire grid from a list of declarative configurations.

        This method acts as the primary entrypoint for future no-code / JSON
        config loaders.
        """
        self.clear_grid()
        for cfg in configs:
            self.add_widget(
                widget=cfg.widget,
                row=cfg.row,
                col=cfg.col,
                row_span=cfg.row_span,
                col_span=cfg.col_span,
                min_height=cfg.min_height,
            )

    def clear_grid(self) -> None:
        """Remove all widgets from the grid without destroying the container."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self._items.clear()

    # ── Internal Helpers ────────────────────────────────────────

    def _apply_item(self, cfg: GridItemConfig) -> None:
        """Apply size policies, min height, and add widget to the grid layout."""
        w = cfg.widget
        if cfg.min_height is not None:
            w.setMinimumHeight(cfg.min_height)

        self.grid_layout.addWidget(w, cfg.row, cfg.col, cfg.row_span, cfg.col_span)
