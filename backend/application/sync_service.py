"""
Sync Service (`backend/application/sync_service.py`)

Application service orchestrating data sync cycles across Repository and Orchestrator layers.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from backend.repository.repository import Repository
from backend.orchestrator.orchestrator import DockerWorkerOrchestrator


@dataclass
class SyncResult:
    success: bool
    board_id: int
    sync_period: str
    graphic_contract: Dict[str, Any] = field(default_factory=dict)
    sql_upsert: str = ""
    error: Optional[str] = None


class SyncService:
    def __init__(self, repository: Repository):
        self._repo = repository

    def run_sync(
        self,
        board_id: int,
        start_date: str = "2026-07-01",
        end_date: str = "2026-07-13",
        kpi_config_id: int = 42,
        frontend_target: str = "smartsheet",
    ) -> SyncResult:
        """
        Full sync cycle for a board.
        """
        try:
            encrypted_key = self._repo.get_api_key(board_id) or ""
            existing_dates = self._repo.get_synced_dates(board_id)
            process_records_od = self._repo.get_process_records(board_id)

            orchestrator = DockerWorkerOrchestrator()

            graphic_contract, sql_upsert, kpi_record_for_db = orchestrator.run_sync_cycle(
                board_id=board_id,
                kpi_config_id=kpi_config_id,
                requested_start_date=start_date,
                requested_end_date=end_date,
                existing_db_dates=existing_dates,
                existing_db_process_data_od=process_records_od,
                encrypted_api_key=encrypted_key,
                kpi_config={"total_ideal_points": 100.0},
            )

            missing = orchestrator.identify_missing_date_gap(start_date, end_date, existing_dates)
            self._repo.add_synced_dates(board_id, missing)

            if frontend_target == "smartsheet" and graphic_contract:
                import subprocess
                import sys
                import json

                payload = json.dumps({"board_id": board_id, "graphic_contract": graphic_contract})
                cmd = [sys.executable, "-m", "backend.publisher.smartsheet_publisher"]

                subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True
                ).communicate(input=payload)

            return SyncResult(
                success=True,
                board_id=board_id,
                sync_period=f"{start_date} -> {end_date}",
                graphic_contract=graphic_contract,
                sql_upsert=sql_upsert,
            )

        except Exception as e:
            return SyncResult(
                success=False,
                board_id=board_id,
                sync_period=f"{start_date} -> {end_date}",
                error=str(e),
            )

    def get_latest_contract(
        self,
        board_id: int,
        start_date: str = "2026-07-01",
        end_date: str = "2026-07-13",
    ) -> Optional[Dict[str, Any]]:
        """
        Read-side projection query.
        """
        db_records_od = self._repo.get_process_records(board_id)
        if not db_records_od:
            return None

        orchestrator = DockerWorkerOrchestrator()
        return orchestrator.compute_contract_from_db_records(
            board_id=board_id,
            kpi_config={"total_ideal_points": 100.0},
            start_date=start_date,
            end_date=end_date,
            existing_db_process_data_od=db_records_od,
        )

    def store_encrypted_key(self, board_id: int, raw_api_key: str) -> Dict[str, Any]:
        """Encrypt and persist an API key via Repository."""
        codec = DockerWorkerOrchestrator().key_codec
        encrypted = codec.encrypt_key(raw_api_key)
        self._repo.save_api_key(board_id, encrypted)
        return {
            "board_id": board_id,
            "encrypted_string_preview": encrypted[:24] + "...",
        }
