"""
repositories.mock.mock_sqdp_repository
======================================
Mock repository for SQDP board data.

Implements the duck-typed repository contract:
    * get_data(**filters) -> Optional[SqdpBoardModel]
    * save_data(data) -> bool
"""

import random
from typing import List, Tuple, Optional, Any
from models.sqdp_models import SqdpLetterModel, SqdpBoardModel


# Standard letter shapes matching the 13-cell agile board
_S_CELLS: List[Tuple[int, int]] = [
    (0, 2), (0, 1), (0, 0),  # 1, 2, 3 (top bar)
    (1, 0), (2, 0), (3, 0),  # 4, 5, 6 (left bar)
    (3, 1), (3, 2),          # 7, 8 (middle bar)
    (4, 2), (5, 2), (6, 2),  # 9, 10, 11 (right bar)
    (6, 1), (6, 0),          # 12, 13 (bottom bar)
] # 13 cells, 7 rows x 3 cols

_Q_CELLS: List[Tuple[int, int]] = [
    (0, 1), (0, 2),          # 1, 2 (top)
    (1, 3), (2, 3), (3, 3), (4, 3),  # 3, 4, 5, 6 (right side)
    (5, 2), (6, 1),          # 7, 8 (bottom curve)
    (5, 0), (3, 0), (1, 0),  # 9, 10, 11 (left side)
    (4, 1),                  # 12 (tail start inside loop)
    (6, 3),                  # 13 (tail bottom right corner)
] # 13 cells, 7 rows x 4 cols

_D_CELLS: List[Tuple[int, int]] = [
    (0, 0), (0, 1),          # 1, 2 (top bar from left corner)
    (1, 2), (2, 2), (3, 2), (4, 2), (5, 2),  # 3, 4, 5, 6, 7 (right arc)
    (6, 1), (6, 0),          # 8, 9 (bottom curve to bottom left corner)
    (5, 0), (4, 0), (3, 0), (1, 0),  # 10, 11, 12, 13 (left spine going up to top left)
] # 13 cells, 7 rows x 3 cols

_P_CELLS: List[Tuple[int, int]] = [
    (2, 2), (2, 3), (1, 3),  # 1, 2, 3 (loop bottom & right)
    (0, 3), (0, 2), (0, 1), (0, 0),  # 4, 5, 6, 7 (top bar)
    (1, 0), (2, 0), (3, 0),  # 8, 9, 10 (upper spine)
    (4, 0), (5, 0), (6, 0),  # 11, 12, 13 (lower spine)
] # 13 cells, 7 rows x 4 cols


class MockSqdpRepository:
    """Mock repository providing simulated SQDP board data.

    Any class with get_data() and save_data() satisfies the repository
    contract via Python duck typing.
    """

    def __init__(self) -> None:
        # In-memory storage for simulated persistence during Phase 1
        self._storage: dict[str, SqdpBoardModel] = {}

    def get_data(self, **filters: Any) -> Optional[SqdpBoardModel]:
        """Retrieve SQDP board data based on filters.

        Parameters
        ----------
        time_range : str, optional
            One of 'daily', 'sprint_1w', 'sprint_2w'. Defaults to 'daily'.
        team : str, optional
            Team identifier for filtering (reserved for multi-team expansion).
        """
        time_range = filters.get("time_range", "daily")
        
        # Check if we already have modified/saved data in memory
        if time_range in self._storage:
            return self._storage[time_range]

        titles = {
            "sprint_1w": "SQDP Sprint 1 Week",
            "sprint_2w": "SQDP Sprints / Quarter (13 Weeks)",
            "daily": "SQDP Daily",
        }
        
        letters = [
            self._make_letter("S", "Safety",       7, 3, _S_CELLS),
            self._make_letter("Q", "Quality",      7, 4, _Q_CELLS),
            self._make_letter("D", "Delivery",     7, 3, _D_CELLS),
            self._make_letter("P", "Productivity", 7, 4, _P_CELLS),
        ]
        
        board = SqdpBoardModel(
            title=titles.get(time_range, "SQDP"),
            time_range=time_range,
            letters=letters,
        )
        self._storage[time_range] = board
        return board

    def save_data(self, data: Any) -> bool:
        """Persist SQDP board data to in-memory storage."""
        if isinstance(data, SqdpBoardModel):
            self._storage[data.time_range] = data
            return True
        return False

    def _make_letter(self, char: str, label: str, rows: int, cols: int,
                     cells: List[Tuple[int, int]]) -> SqdpLetterModel:
        """Helper to create a letter model with randomized cell statuses."""
        status = [random.choice([0, 1]) for _ in range(len(cells))]
        return SqdpLetterModel(
            char=char, label=label, rows=rows, cols=cols,
            cells=cells, status=status,
        )
