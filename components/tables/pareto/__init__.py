"""
components.tables.pareto
========================
Pareto table variants: dashboard read-only, user-input, admin-review, category reading, and creation log.
"""

from .pareto_table import ParetoTable
from .pareto_table_user import ParetoTableUser
from .pareto_table_admin import ParetoTableAdmin
from .pareto_category_table import ParetoCategoryTable
from .pareto_table_create import ParetoTableCreate

__all__ = [
    "ParetoTable",
    "ParetoTableUser",
    "ParetoTableAdmin",
    "ParetoCategoryTable",
    "ParetoTableCreate",
]
