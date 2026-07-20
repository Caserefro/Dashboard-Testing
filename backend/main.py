"""
Project ATLAS - REST API Transport Layer (`backend/main.py`)

Thin FastAPI handlers responsible ONLY for:
  - Request parsing & validation (Pydantic models)
  - HTTP response formatting & status codes
  - Delegating use-case logic to SyncService

Does NOT contain business logic, storage resolution, or orchestrator calls.
"""

from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.dependencies import sync_service

# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Project ATLAS - Data Sync & Orchestration API",
    description="24/7 Pure Factory Orchestration Engine for Agile KPI Analytics",
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# Request / Response models (transport concern only)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Endpoints — thin handlers, delegate immediately to SyncService
# ---------------------------------------------------------------------------


@app.post("/SYNC")
def trigger_sync_post(req: SyncRequest) -> Dict[str, Any]:
    """POST /SYNC — triggers a full extraction + analysis cycle."""
    result = sync_service.run_sync(
        board_id=req.board_id,
        start_date=req.start_date,
        end_date=req.end_date,
        kpi_config_id=req.kpi_config_id,
        output_format=req.output_format,
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=f"SyncError: {result.error}")

    return {
        "status": "success",
        "board_id": result.board_id,
        "sync_period": result.sync_period,
        "ui_graph_contracts": result.graphic_contract,
        "generated_sql_upsert": result.sql_upsert,
    }


@app.get("/SYNC")
def trigger_sync_get(
    board_id: int = Query(10, description="Board ID to sync"),
    start_date: str = Query("2026-07-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2026-07-13", description="End date YYYY-MM-DD"),
    output_format: str = Query("graphic_contract", description="Output shape"),
    kpi_config_id: int = Query(42, description="Config ID for Postgres table"),
) -> Dict[str, Any]:
    """GET /SYNC — browser-friendly trigger."""
    result = sync_service.run_sync(
        board_id=board_id,
        start_date=start_date,
        end_date=end_date,
        kpi_config_id=kpi_config_id,
        output_format=output_format,
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=f"SyncError: {result.error}")

    return {
        "status": "success",
        "board_id": result.board_id,
        "sync_period": result.sync_period,
        "ui_graph_contracts": result.graphic_contract,
        "generated_sql_upsert": result.sql_upsert,
    }


@app.post("/api/config/keys")
def configure_encrypted_key(req: KeyConfigRequest) -> Dict[str, Any]:
    """Encrypt and store a raw PAT token for a board."""
    try:
        info = sync_service.store_encrypted_key(req.board_id, req.raw_api_key)
        return {
            "status": "success",
            "board_id": req.board_id,
            "vendor_type": req.vendor_type,
            "message": "API key successfully encrypted and stored. Zero raw token exposure.",
            "encrypted_string_preview": info["encrypted_string_preview"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KeyEncryptionError: {str(e)}")


@app.get("/api/kpis/latest")
def get_latest_graph_contract(
    board_id: int = Query(10, description="Board ID to query"),
) -> Dict[str, Any]:
    """Return the most recently cached graphic contract for a board."""
    contract = sync_service.get_latest_contract(board_id)
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail=f"No graph contract found for Board ID {board_id}. Run /SYNC first.",
        )
    return contract
