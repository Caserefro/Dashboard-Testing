"""
Project ATLAS - Master REST API Server (`backend/main.py`)

Exposes the exact endpoints defined in the architectural design:
  1. `/SYNC` (POST & GET): Receives Board ID + Time Period, recovers encrypted keys from DB/config,
     decrypts via KeyCodec, packages payload, triggers DockerWorkerOrchestrator, and returns `ui_graph_contracts` (`graphic_contract`).
  2. `/api/config/keys` (POST): Configurator endpoint for Qt 5 / Admin tools to safely encrypt raw Azure/GitHub API tokens.
  3. `/api/kpis/latest` (GET): Retrieves the last computed graph contract for UI rendering.
"""

from typing import Dict, Any, Optional, Set
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from backend.orchestrator.daemon import DockerWorkerOrchestrator
from backend.test_backend_pipeline import SAMPLE_RAW_JSON, SAMPLE_OD, SAMPLE_AZURE_PR_JSON

app = FastAPI(
    title="Project ATLAS - Data Sync & Orchestration API",
    description="24/7 Pure Factory Orchestration Engine for Agile KPI Analytics & Azure DevOps Integration",
    version="1.0.0"
)

# Initialize Orchestrator in Single Container / In-Memory mode for ultra-fast, zero-socket execution
orchestrator = DockerWorkerOrchestrator(use_docker_containers=False, master_key_base64="my-secret-master-key")

# In-memory store simulating our Postgres `KPI_CONFIGS` and `KPI_RECORDS_DAILY` tables before DB connection string is plugged in
_IN_MEMORY_DB_KEYS: Dict[int, str] = {
    10: orchestrator.key_codec.encrypt_key("default_azure_pat_token_for_board_10")
}
_IN_MEMORY_DB_DATES: Dict[int, Set[str]] = {
    10: {"2026-07-01", "2026-07-02"}
}
_IN_MEMORY_LATEST_CONTRACTS: Dict[int, Dict[str, Any]] = {}


class SyncRequest(BaseModel):
    """Payload model for the /SYNC endpoint."""
    board_id: int = 10
    start_date: str = "2026-07-01"
    end_date: str = "2026-07-13"
    output_format: str = "graphic_contract"
    kpi_config_id: int = 42


class KeyConfigRequest(BaseModel):
    """Payload model for the Qt Configurator API key encryption endpoint."""
    board_id: int
    raw_api_key: str
    vendor_type: str = "azure_devops"


@app.post("/SYNC")
def trigger_sync_cycle_post(req: SyncRequest) -> Dict[str, Any]:
    """
    Master /SYNC Endpoint (POST).
    1. Recovers encrypted string from DB/config for requested `board_id`.
    2. Decrypts key & packages `missing_dates` + API key for the Azure API extractor.
    3. Runs Normalizer -> Analizer -> Parser.
    4. Returns Data in the format of `ui_graph_contracts` (`graphic_contract`) along with generated SQL UPSERT.
    """
    return _execute_sync_flow(
        board_id=req.board_id,
        start_date=req.start_date,
        end_date=req.end_date,
        output_format=req.output_format,
        kpi_config_id=req.kpi_config_id
    )


@app.get("/SYNC")
def trigger_sync_cycle_get(
    board_id: int = Query(10, description="Board ID to sync"),
    start_date: str = Query("2026-07-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2026-07-13", description="End date YYYY-MM-DD"),
    output_format: str = Query("graphic_contract", description="Output shape: graphic_contract, csv, or html"),
    kpi_config_id: int = Query(42, description="Config ID for Postgres table")
) -> Dict[str, Any]:
    """Master /SYNC Endpoint (GET support for easy browser & URL triggering)."""
    return _execute_sync_flow(board_id, start_date, end_date, output_format, kpi_config_id)


def _execute_sync_flow(board_id: int, start_date: str, end_date: str, output_format: str, kpi_config_id: int) -> Dict[str, Any]:
    try:
        # Step 1: Recover encrypted string from DB for `board_id`
        if board_id not in _IN_MEMORY_DB_KEYS:
            # Fallback auto-enroll if board not yet configured
            _IN_MEMORY_DB_KEYS[board_id] = orchestrator.key_codec.encrypt_key(f"auto_pat_for_board_{board_id}")
            _IN_MEMORY_DB_DATES[board_id] = set()

        encrypted_api_key = _IN_MEMORY_DB_KEYS[board_id]
        existing_dates = _IN_MEMORY_DB_DATES[board_id]

        # Combine our sample ticket and PR fixtures to simulate live extractor payload during testing
        combined_raw_json = {
            "workItems": SAMPLE_RAW_JSON["workItems"],
            "pullRequests": SAMPLE_AZURE_PR_JSON["pullRequests"],
            "repo": SAMPLE_AZURE_PR_JSON["repo"]
        }

        # Step 2 & 3: Run Orchestrator Sync Cycle (`Normalizer -> Analizer -> Parser`)
        graphic_contract, sql_upsert = orchestrator.run_sync_cycle(
            board_id=board_id,
            kpi_config_id=kpi_config_id,
            requested_start_date=start_date,
            requested_end_date=end_date,
            existing_db_dates=existing_dates,
            existing_db_process_data_od=SAMPLE_OD,
            encrypted_api_key=encrypted_api_key,
            kpi_config={"total_ideal_points": 100.0}
        )

        # Cache contract for visual UI rendering
        _IN_MEMORY_LATEST_CONTRACTS[board_id] = graphic_contract

        return {
            "status": "success",
            "board_id": board_id,
            "sync_period": f"{start_date} -> {end_date}",
            "ui_graph_contracts": graphic_contract,
            "generated_sql_upsert": sql_upsert
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OrchestratorSyncError: {str(e)}")


@app.post("/api/config/keys")
def configure_encrypted_key(req: KeyConfigRequest) -> Dict[str, Any]:
    """
    Configurator Endpoint for Qt 5 Desktop App / Security Admins.
    Takes a raw PAT token (`raw_api_key`), encrypts it via KeyCodec (`AES Hephaestus`), and stores safe string.
    """
    try:
        encrypted = orchestrator.key_codec.encrypt_key(req.raw_api_key)
        _IN_MEMORY_DB_KEYS[req.board_id] = encrypted
        return {
            "status": "success",
            "board_id": req.board_id,
            "vendor_type": req.vendor_type,
            "message": "API key successfully encrypted and stored. Zero raw token exposure.",
            "encrypted_string_preview": encrypted[:24] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KeyEncryptionError: {str(e)}")


@app.get("/api/kpis/latest")
def get_latest_graph_contract(board_id: int = Query(10, description="Board ID to query")) -> Dict[str, Any]:
    """Returns the last computed ui_graph_contracts for instant UI rendering."""
    if board_id not in _IN_MEMORY_LATEST_CONTRACTS:
        raise HTTPException(status_code=404, detail=f"No graph contract found for Board ID {board_id}. Run /SYNC first.")
    return _IN_MEMORY_LATEST_CONTRACTS[board_id]
