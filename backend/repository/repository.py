"""
Infrastructure Repository (`backend/repository/repository.py`)

Singleton entity that owns all persistent storage access.
Thread-safe: multiple Orchestrator facades can read/write concurrently
without corrupting shared state.

Currently backed by in-memory dicts (swap internals for psycopg3 later).
The rest of the application never touches storage directly, maintaining strict Domain isolation.
"""

import threading
from typing import Dict, Any, Set, List, Optional


class Repository:

    def __init__(self):
        self._lock = threading.Lock()

        # In-memory backing stores (replace with psycopg3 pool later)
        self._api_keys: Dict[int, str] = {}
        self._synced_dates: Dict[int, Set[str]] = {}
        self._process_records: Dict[int, List[Dict[str, Any]]] = {}

    # ── API Keys ──────────────────────────────────────────────────────

    def get_api_key(self, board_id: int) -> Optional[str]:
        with self._lock:
            return self._api_keys.get(board_id)

    def save_api_key(self, board_id: int, encrypted_key: str) -> None:
        with self._lock:
            self._api_keys[board_id] = encrypted_key

    # ── Synced Dates (for SQL Gap Detection) ──────────────────────────

    def get_synced_dates(self, board_id: int) -> Set[str]:
        with self._lock:
            return set(self._synced_dates.get(board_id, set()))

    def add_synced_dates(self, board_id: int, dates: List[str]) -> None:
        with self._lock:
            if board_id not in self._synced_dates:
                self._synced_dates[board_id] = set()
            self._synced_dates[board_id].update(dates)

    # ── Process Records (Historical OD for Analyzer) ──────────────────

    def get_process_records(self, board_id: int) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._process_records.get(board_id, []))

    def save_process_record(self, board_id: int, record: Dict[str, Any]) -> None:
        with self._lock:
            if board_id not in self._process_records:
                self._process_records[board_id] = []
            self._process_records[board_id].append(record)

    # ── Seed (for testing / initial mock data) ────────────────────────

    def seed(
        self,
        board_id: int,
        api_key: str,
        synced_dates: Set[str],
        process_records: List[Dict[str, Any]],
    ) -> None:
        with self._lock:
            self._api_keys[board_id] = api_key
            self._synced_dates[board_id] = synced_dates
            self._process_records[board_id] = process_records
