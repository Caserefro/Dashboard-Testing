"""WOR Dashboard shared data models.

This package contains **typed dataclass DTOs** consumed by graphic
widgets.  Every model is a plain data container — it carries no
business logic, validation, or persistence concerns.

Shared terminology
------------------
title
    Human-readable heading rendered at the top of a widget.
categories
    Ordered labels for the X-axis or row dimension.
values
    Numeric data aligned 1-to-1 with *categories*.
time_range
    Temporal granularity selector:
    ``'daily'`` (31 cells), ``'sprint_1w'`` (7), ``'sprint_2w'`` (14).
"""

# SQDP board models
from .sqdp_models import SqdpLetterModel, SqdpBoardModel

# Chart models
from .chart_models import BarChartModel, ProgressBarChartModel, BurndownChartModel, SafetyBarChartModel

# Table models
from .table_models import (
    ParetoTableModel,
    SafetyFieldModel,
    SafetyTableModel,
    TextGuideColumnModel,
    TextGuideTableModel,
    SafetyQuestionModel,
    SafetyQuestionnaireModel,
)

__all__ = [
    # SQDP
    "SqdpLetterModel",
    "SqdpBoardModel",
    # Charts
    "BarChartModel",
    "ProgressBarChartModel",
    "BurndownChartModel",
    "SafetyBarChartModel",
    # Tables
    "ParetoTableModel",
    "SafetyFieldModel",
    "SafetyTableModel",
    "TextGuideColumnModel",
    "TextGuideTableModel",
    "SafetyQuestionModel",
    "SafetyQuestionnaireModel",
]
