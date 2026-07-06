"""
components.sqdp
===============
SQDP graphic component family.

Exports the abstract base and all three concrete SQDP renderers:

* :class:`BaseSqdpWidget`     — shared letter-grid painting logic
* :class:`Sprint1WSqdpWidget` — 1-week sprint (7 cells per letter)
* :class:`Sprint2WSqdpWidget` — 2-week sprint (14 cells per letter)
* :class:`DailySqdpWidget`    — daily tracking (up to 31 cells per letter)
"""

from .base_sqdp import BaseSqdpWidget
from .sprint_1w_sqdp import Sprint1WSqdpWidget
from .sprint_2w_sqdp import Sprint2WSqdpWidget
from .daily_sqdp import DailySqdpWidget

__all__ = [
    "BaseSqdpWidget",
    "Sprint1WSqdpWidget",
    "Sprint2WSqdpWidget",
    "DailySqdpWidget",
]
