"""
repositories.mock.mock_chart_repository
=======================================
Mock repository for chart data (Bar Charts, Progress Combo, Burndown).

Implements the duck-typed repository contract:
    * get_data(**filters) -> Optional[Any]
    * save_data(data) -> bool
"""

import random
import numpy as np
from scipy.interpolate import PchipInterpolator
from typing import Optional, Any, List
from models.chart_models import BarChartModel, ProgressBarChartModel, BurndownChartModel


class MockChartRepository:
    """Mock repository providing simulated chart data models."""

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}

    def get_data(self, **filters: Any) -> Optional[Any]:
        """Retrieve chart model based on chart_type filter.

        Parameters
        ----------
        chart_type : str
            One of 'bar', 'sqdp_bar', 'progress', 'burndown'.
        """
        chart_type = filters.get("chart_type", "bar")

        if chart_type in self._storage:
            return self._storage[chart_type]

        if chart_type in ("bar", "sqdp_bar", "efficiency"):
            model = self._generate_bar_chart()
        elif chart_type == "progress":
            model = self._generate_progress_chart()
        elif chart_type == "burndown":
            model = self._generate_burndown_chart()
        else:
            return None

        self._storage[chart_type] = model
        return model

    def save_data(self, data: Any) -> bool:
        """Persist chart model to in-memory storage."""
        if isinstance(data, BarChartModel):
            self._storage["bar"] = data
            return True
        elif isinstance(data, ProgressBarChartModel):
            self._storage["progress"] = data
            return True
        elif isinstance(data, BurndownChartModel):
            self._storage["burndown"] = data
            return True
        return False

    def _generate_bar_chart(self) -> BarChartModel:
        n_weeks = random.randint(8, 16)
        return BarChartModel(
            title="Productivity: How efficient are we being?",
            x_label="Weeks",
            categories=[str(i) for i in range(1, n_weeks + 1)],
            values=[round(random.uniform(0.45, 1.0), 2) for _ in range(n_weeks)],
            target_threshold=0.8,
            y_max=1.0,
        )

    def _generate_progress_chart(self) -> ProgressBarChartModel:
        n = random.randint(15, 30)
        categories = [str(i) for i in range(14, 14 + n)]
        bar_values = [float(random.randint(80, 180)) for _ in range(n)]

        completed = []
        total = []
        c_val = random.randint(250, 300)
        t_val = c_val + random.randint(50, 100)
        for _ in range(n):
            c_val += random.randint(2, 8)
            t_val += random.randint(4, 10)
            completed.append(float(c_val))
            total.append(float(t_val))

        return ProgressBarChartModel(
            title="ESC-A Verification Progress Inc. Year",
            x_label="Quarter",
            categories=categories,
            bar_values=bar_values,
            line_completed=completed,
            line_total=total,
            y_max=float(max(max(total), max(bar_values)) * 1.15),
        )

    def _generate_burndown_chart(self) -> BurndownChartModel:
        N = 10
        x_checkpoints = np.linspace(0.0, 1.0, N)
        y_avg = np.array([100.0, 94.3, 93.1, 91.4, 90.6, 89.3, 85.4, 73.5, 35.5, 2.2])

        master_pchip = PchipInterpolator(x_checkpoints, y_avg)
        x_smooth = [i / 100.0 for i in range(101)]
        line_master = [float(master_pchip(x)) for x in x_smooth]

        live_idx = 6
        x_live = [float(x) for x in x_checkpoints[:live_idx]]
        y_live = [100.0, 101.5, 102.1, 101.8, 98.4, 99.7]
        current_delta = y_live[-1] - y_avg[live_idx - 1]

        start_x = x_live[-1]
        n_future = 50
        x_future = [start_x + (1.0 - start_x) * (i / (n_future - 1)) for i in range(n_future)]

        line_slip = [float(master_pchip(x) + current_delta) for x in x_future]
        line_catchup = []
        for x in x_future:
            decay = (1.0 - x) / (1.0 - start_x) if x < 1.0 else 0.0
            line_catchup.append(float(master_pchip(x) + current_delta * decay))

        return BurndownChartModel(
            title="Method 3: Approximating Burndown & Agile Delta Forecast",
            x_label="Sprint Progress (%)",
            y_label="Remaining Work (Points)",
            x_categories=["0%", "20%", "40%", "60%", "80%", "100%"],
            x_smooth=x_smooth,
            line_master=line_master,
            x_live=x_live,
            y_live=y_live,
            x_future=x_future,
            line_slip=line_slip,
            line_catchup=line_catchup,
            y_max=120.0,
            deadline_delta=round(current_delta, 1),
        )
