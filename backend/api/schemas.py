"""
API Transport Schemas (`backend/api/schemas.py`)

Pydantic request and response DTO models for REST endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class SyncRequest(BaseModel):
    """Payload model for the /SYNC endpoint."""
    board_id: int = Field(default=10, description="Target board identifier")
    start_date: str = Field(default="2026-07-01", description="Start date YYYY-MM-DD")
    end_date: str = Field(default="2026-07-13", description="End date YYYY-MM-DD")
    output_format: str = Field(default="graphic_contract", description="Desired output format")
    kpi_config_id: int = Field(default=42, description="KPI configuration ID")


class KeyConfigRequest(BaseModel):
    """Payload model for the API key encryption endpoint."""
    board_id: int = Field(description="Target board identifier")
    raw_api_key: str = Field(description="Raw PAT token to encrypt")
    vendor_type: str = Field(default="azure_devops", description="Vendor type string")


class SprintCalendarRequest(BaseModel):
    """Payload model for the sprint calendar date grid endpoint."""
    board_id: int = Field(default=10, description="Target board identifier")
    project_number: int = Field(default=1, description="GitHub Project V2 number")
    org: str = Field(default="", description="GitHub Organization name if applicable")
    repo: str = Field(default="owner/repo", description="GitHub Repository name")
