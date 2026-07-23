"""
API Routes (`backend/api/routes.py`)

FastAPI HTTP endpoint handlers responsible ONLY for:
  - Request parsing & validation
  - Delegating business use-case logic to Application Services
  - Formatting HTTP responses & status codes
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import SyncRequest, KeyConfigRequest, SprintCalendarRequest
from backend.dependencies import sync_service, sprint_calendar_service, excel_sprint_calendar_service

router = APIRouter()


@router.post("/SYNC")
def trigger_sync_post(req: SyncRequest) -> Dict[str, Any]:
    """POST /SYNC — triggers a full extraction + analysis cycle."""
    result = sync_service.run_sync(
        board_id=req.board_id,
        start_date=req.start_date,
        end_date=req.end_date,
        kpi_config_id=req.kpi_config_id,
        frontend_target="smartsheet" if req.output_format == "graphic_contract" else req.output_format,
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


@router.get("/SYNC")
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
        frontend_target="smartsheet" if output_format == "graphic_contract" else output_format,
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


@router.post("/api/config/keys")
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


@router.get("/api/kpis/latest")
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
    if isinstance(contract, str):
        import json
        contract = json.loads(contract)
    return contract


@router.post("/api/sprints/calendar")
def get_sprint_calendar_grid(req: SprintCalendarRequest) -> Dict[str, Any]:
    """Return Excel 2-column calendar skeleton rows (record_date, Sprint) for a project."""
    try:
        payload = {
            "board_id": req.board_id,
            "projectNumber": req.project_number,
            "org": req.org,
            "repo": req.repo
        }
        sprints = sprint_calendar_service.get_sprints_via_graphql(payload)
        
        calendar_grid = []
        for sinfo in sprints:
            rows = excel_sprint_calendar_service.generate_excel_calendar_rows(sinfo)
            calendar_grid.append({
                "sprint": sinfo.title,
                "start_date": sinfo.start_date,
                "end_date": sinfo.end_date,
                "excel_skeleton_rows": rows
            })
            
        return {
            "status": "success",
            "board_id": req.board_id,
            "sprints": calendar_grid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SprintCalendarError: {str(e)}")
