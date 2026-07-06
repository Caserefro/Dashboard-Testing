"""
components.tables.pareto
========================
Pareto table variants: dashboard read-only, user-input, and admin-review.
"""

from .pareto_table import ParetoTable
from .pareto_table_user import ParetoTableUser
from .pareto_table_admin import ParetoTableAdmin

__all__ = ["ParetoTable", "ParetoTableUser", "ParetoTableAdmin"]
