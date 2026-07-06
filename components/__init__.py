"""WOR Dashboard graphic components.

This package provides independent, SOLID graphic modules organized
into three families: SQDP graphs, bar charts, and tables.
Each component is a self-contained QWidget that renders a typed
data model without performing any business logic.
"""

from .selection_widget import DynamicSelectWidget
from .dashboard_grid import ScrollableDashboardGrid, GridItemConfig

__all__ = [
    "DynamicSelectWidget",
    "ScrollableDashboardGrid",
    "GridItemConfig",
]
