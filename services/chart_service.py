"""
services.chart_service
======================
Business logic layer for chart widgets (Bar, Progress Combo, Burndown).

Receives any repository object implementing `get_data` and `save_data`
via constructor dependency injection. Wraps calls in try/except blocks.
"""

from typing import Any, Optional


class ChartService:
    """Service layer responsible for fetching and processing Chart models.

    Parameters
    ----------
    repository : Any
        A duck-typed repository instance providing `get_data` and `save_data`.
    """

    def __init__(self, repository: Any) -> None:
        self._repo = repository

    def get_processed_data(self, **params: Any) -> Optional[Any]:
        """Fetch chart data from repository with robust error handling.

        Parameters
        ----------
        chart_type : str
            'bar', 'progress', or 'burndown'.
        """
        try:
            raw_model = self._repo.get_data(**params)
            if not raw_model:
                return None
            return raw_model
        except AttributeError as e:
            print(f"[ChartService] Repository contract violation: missing method -> {e}")
            return None
        except Exception as e:
            print(f"[ChartService] Error fetching chart data: {e}")
            return None

    def save_data(self, model: Any) -> bool:
        """Persist updated chart model."""
        try:
            return self._repo.save_data(model)
        except Exception as e:
            print(f"[ChartService] Error saving chart data: {e}")
            return False
