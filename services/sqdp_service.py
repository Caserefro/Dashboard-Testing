"""
services.sqdp_service
=====================
Business logic layer for SQDP board widgets.

Receives any repository object implementing `get_data` and `save_data`
via constructor dependency injection. Wraps calls in try/except blocks
to ensure UI stability.
"""

from typing import Any, Optional
from models.sqdp_models import SqdpBoardModel


class SqdpService:
    """Service layer responsible for fetching and processing SQDP models.

    Parameters
    ----------
    repository : Any
        A duck-typed repository instance providing `get_data` and `save_data`.
    """

    def __init__(self, repository: Any) -> None:
        self._repo = repository

    def get_processed_data(self, **params: Any) -> Optional[SqdpBoardModel]:
        """Fetch SQDP data from repository with robust error handling.

        Parameters
        ----------
        time_range : str, optional
            'daily', 'sprint_1w', or 'sprint_2w'.
        """
        try:
            raw_model = self._repo.get_data(**params)
            if not raw_model:
                return None
            return raw_model
        except AttributeError as e:
            print(f"[SqdpService] Repository contract violation: missing method -> {e}")
            return None
        except Exception as e:
            print(f"[SqdpService] Error fetching SQDP data: {e}")
            return None

    def save_data(self, model: SqdpBoardModel) -> bool:
        """Persist updated SQDP board model."""
        try:
            return self._repo.save_data(model)
        except Exception as e:
            print(f"[SqdpService] Error saving SQDP data: {e}")
            return False
