"""
services.table_service
======================
Business logic layer for table widgets (Pareto Loss Table, Safety Table).

Receives any repository object implementing `get_data` and `save_data`
via constructor dependency injection. Wraps calls in try/except blocks.
"""

from typing import Any, Optional


class TableService:
    """Service layer responsible for fetching and processing Table models.

    Parameters
    ----------
    repository : Any
        A duck-typed repository instance providing `get_data` and `save_data`.
    """

    def __init__(self, repository: Any) -> None:
        self._repo = repository

    def get_processed_data(self, **params: Any) -> Optional[Any]:
        """Fetch table data from repository with robust error handling.

        Parameters
        ----------
        table_type : str
            'pareto' or 'safety'.
        """
        try:
            raw_model = self._repo.get_data(**params)
            if not raw_model:
                return None
            return raw_model
        except AttributeError as e:
            print(f"[TableService] Repository contract violation: missing method -> {e}")
            return None
        except Exception as e:
            print(f"[TableService] Error fetching table data: {e}")
            return None

    def save_data(self, model: Any) -> bool:
        """Persist updated table model."""
        try:
            return self._repo.save_data(model)
        except Exception as e:
            print(f"[TableService] Error saving table data: {e}")
            return False
