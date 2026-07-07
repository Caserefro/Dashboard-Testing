"""
components.tables
=================
Table graphic component family for the dashboard.

Re-exports every public table widget so consumers can do::

    from components.tables import ParetoTable, SafetyTable, ParetoCategoryTable
"""

from .base_table import BaseTableWidget
from .pareto import (
    ParetoTable,
    ParetoTableUser,
    ParetoTableAdmin,
    ParetoCategoryTable,
    ParetoTableCreate,
)
from .safety import (
    SafetyTable,
    SafetyTableUser,
    SafetyTableFocal,
    SafetyAnswerWidget,
    SafetyQuestionWidget,
    SafetyQuestionnaireWidget,
)
from .guide_table import TextGuideTable, SafetyGuideTable, ParetoTableGuide

__all__ = [
    "BaseTableWidget",
    "ParetoTable",
    "ParetoTableUser",
    "ParetoTableAdmin",
    "ParetoCategoryTable",
    "ParetoTableCreate",
    "SafetyTable",
    "SafetyTableUser",
    "SafetyTableFocal",
    "SafetyAnswerWidget",
    "SafetyQuestionWidget",
    "SafetyQuestionnaireWidget",
    "TextGuideTable",
    "SafetyGuideTable",
    "ParetoTableGuide",
]
