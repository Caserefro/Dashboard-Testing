"""
Application Wiring (`backend/dependencies.py`)

Creates the singleton instances (Repository, SyncService) once at import time.
Both the HTTP handler (`main.py`) and background workers (`nightly_worker.py`)
import from here to get the same shared singletons.
"""

from backend.repository.repository import Repository
from backend.application_layer import SyncService
from backend.test_backend_pipeline import SAMPLE_OD

# Singletons
repository = Repository()
sync_service = SyncService(repository)

# Seed board 10 with mock data for development
repository.seed(
    board_id=10,
    api_key="mock_encrypted_pat_for_board_10",
    synced_dates={"2026-07-01", "2026-07-02"},
    process_records=SAMPLE_OD,
)
