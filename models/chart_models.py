"""Chart data models.

Dataclass DTOs for bar-chart and progress-chart graphic components.
Values are pre-computed by the business layer; the graphic widget
only reads these fields for rendering.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BarChartModel:
    """Data model for a threshold-based bar chart.

    Used for efficiency / productivity charts where bars are
    colour-coded based on their value relative to *target_threshold*.

    Colour logic (implemented by the widget, **not** this model):
        * value >= target_threshold  → green (on target)
        * value <  target_threshold  → red (below target / miss)

    Attributes:
        title: Chart title displayed at the top.
        x_label: Label for the X-axis.
        categories: List of category labels for the X-axis
                    (e.g. week numbers).
        values: List of numeric values, one per category.
        target_threshold: Values at or above this are green; below are red.
        y_max: Maximum Y-axis value for scaling.  Defaults to ``1.0``.
    """

    title: str
    x_label: str
    categories: List[str]
    values: List[float]
    target_threshold: float
    y_max: float = 1.0

    def __post_init__(self) -> None:
        if len(self.categories) != len(self.values):
            raise ValueError(
                f"BarChartModel length mismatch: categories ({len(self.categories)}) "
                f"vs values ({len(self.values)}) must be equal length."
            )


@dataclass
class ProgressBarChartModel:
    """Data model for a progress combo chart (bars + tracking lines).

    Combines vertical bars (periodic output) with two tracking lines:
    one for cumulative actual progress and one for cumulative target.

    Attributes:
        title: Chart title displayed at the top.
        x_label: Label for the X-axis.
        categories: List of category labels for the X-axis.
        bar_values: List of periodic output values (rendered as bars).
        line_completed: List of cumulative actual values (solid line).
        line_total: List of cumulative target values (dashed line).
        y_max: Maximum Y-axis value for scaling.
    """

    title: str
    x_label: str
    categories: List[str]
    bar_values: List[float]
    line_completed: List[float]
    line_total: List[float]
    y_max: float = 500.0

    def __post_init__(self) -> None:
        n = len(self.categories)
        if len(self.bar_values) != n or len(self.line_completed) != n or len(self.line_total) != n:
            raise ValueError(
                f"ProgressBarChartModel length mismatch: categories ({n}), "
                f"bar_values ({len(self.bar_values)}), line_completed ({len(self.line_completed)}), "
                f"and line_total ({len(self.line_total)}) must all be equal length."
            )


@dataclass
class BurndownChartModel:
    """Data model for an Approximating Burndown Curve chart.

    Displays historical master baseline, live sprint checkpoints,
    and agile delta forecast tracks (Catch-Up vs Slip Track).
    All calculations (interpolation, curve fitting, delta decay) are
    pre-computed by the business/analytical layer; this DTO only holds
    data for rendering.

    Attributes:
        title: Chart title displayed at the top.
        x_label: Label for the X-axis (e.g., 'Sprint Progress (%)').
        y_label: Label for the Y-axis (e.g., 'Remaining Work (Points)').
        x_categories: Tick labels for X-axis (e.g., ['0%', '20%', '40%', '60%', '80%', '100%']).
        x_smooth: List of X coordinates (in range 0.0 to 1.0 relative to chart width) for smooth baseline.
        line_master: Smooth Master Baseline Y values corresponding to x_smooth.
        x_live: X coordinates (in range 0.0 to 1.0) for live sprint actual checkpoints.
        y_live: Y coordinates (remaining points) for live sprint actuals.
        x_future: X coordinates (in range 0.0 to 1.0) for future forecast curves.
        line_slip: Y values for Slip Track (parallel offset forecast).
        line_catchup: Y values for Catch-Up Track (tapering delta to 0).
        y_max: Maximum Y-axis value for vertical scaling.
        deadline_delta: Remaining points gap at deadline under slip scenario.
    """

    title: str
    x_label: str
    y_label: str
    x_categories: List[str]
    x_smooth: List[float]
    line_master: List[float]
    x_live: List[float]
    y_live: List[float]
    x_future: List[float]
    line_slip: List[float]
    line_catchup: List[float]
    y_max: float = 120.0
    deadline_delta: float = 0.0

    def __post_init__(self) -> None:
        if len(self.x_smooth) != len(self.line_master):
            raise ValueError(
                f"BurndownChartModel mismatch: x_smooth ({len(self.x_smooth)}) "
                f"vs line_master ({len(self.line_master)}) must be equal length."
            )
        if len(self.x_live) != len(self.y_live):
            raise ValueError(
                f"BurndownChartModel mismatch: x_live ({len(self.x_live)}) "
                f"vs y_live ({len(self.y_live)}) must be equal length."
            )
        if len(self.x_future) != len(self.line_slip) or len(self.x_future) != len(self.line_catchup):
            raise ValueError(
                f"BurndownChartModel mismatch in future forecast curves: x_future ({len(self.x_future)}), "
                f"line_slip ({len(self.line_slip)}), and line_catchup ({len(self.line_catchup)}) must be equal length."
            )


@dataclass
class SafetyBarChartModel:
    """Data model for a stacked Safety SQDP bar chart.

    Each category (e.g. Week) has 4 stacked sub-values representing safety metrics
    (e.g., Motivation, Connected, Workload, Teamwork). The total height of the bar is
    the sum of the 4 sub-values. The outer edges of the bar are colored Green or Red
    depending on whether the total height meets or exceeds the target_threshold.

    Attributes:
        title: Chart title (e.g., 'Safety Assessment: Weekly SQDP Breakdown').
        x_label: X-axis title (e.g., 'Weeks').
        categories: List of category labels (e.g., ['1', '2', ..., '13']).
        sub_values: 2D list [category_idx][4] of numeric values for the 4 stacked segments
                    (from bottom to top: Grey, Dark Blue, Amber, Light Blue).
        target_threshold: Binary threshold line (e.g., 2.5).
        y_max: Upper limit of Y-axis (e.g., 3.0).
        legend_labels: Names of the 4 stacked metrics (default: ['Motivation', 'Connected', 'Workload', 'Teamwork']).
    """

    title: str
    x_label: str
    categories: List[str]
    sub_values: List[List[float]]
    target_threshold: float = 2.5
    y_max: float = 3.0
    legend_labels: List[str] = field(default_factory=lambda: ["Motivation", "Connected", "Workload", "Teamwork"])

    def __post_init__(self) -> None:
        if len(self.sub_values) != len(self.categories):
            raise ValueError(
                f"SafetyBarChartModel mismatch: categories ({len(self.categories)}) "
                f"must match sub_values ({len(self.sub_values)})."
            )
        for i, vals in enumerate(self.sub_values):
            if len(vals) != 4:
                raise ValueError(
                    f"SafetyBarChartModel category index {i} must have exactly 4 sub-values (got {len(vals)})."
                )

