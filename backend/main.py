"""
Project ATLAS - REST API Bootstrap (`backend/main.py`)

FastAPI Application Bootstrap & Entrypoint:
  - Configures FastAPI app metadata & middleware
  - Mounts HTTP transport router from `backend.api`
"""

from fastapi import FastAPI
from backend.api import router

app = FastAPI(
    title="Project ATLAS - Data Sync & Orchestration API",
    description="24/7 Pure Factory Orchestration Engine for Agile KPI Analytics",
    version="2.0.0",
)

# Mount HTTP routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
