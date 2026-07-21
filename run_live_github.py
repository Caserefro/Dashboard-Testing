"""
Live GitHub Runner (`run_live_github.py`)

This script simulates exactly what the Excel VBA macro will execute.
It hits the live GitHub API, runs the pipeline, and spits out a CSV for Excel.
"""

import sys
import json
import os
from backend.worker.worker_factory import AnalyticsWorkerFactory

def main():
    # ==========================================
    # TODO: INSERT YOUR ACTUAL CREDENTIALS HERE
    # ==========================================
    REAL_GITHUB_PAT = "ghp_your_actual_token_here"
    GITHUB_REPO = "Caserefro/Dashboard-Testing"
    PROJECT_NUMBER = 1 # Change this to your actual GitHub Project Number
    
    if REAL_GITHUB_PAT == "ghp_your_actual_token_here":
        print("ERROR: Please open 'run_live_github.py' and insert your real GitHub PAT!")
        sys.exit(1)

    # 1. Simulate the payload coming from the Excel VBA Button
    payload = {
        "api_key": REAL_GITHUB_PAT,
        "repo": GITHUB_REPO,
        "projectNumber": PROJECT_NUMBER,
        "org": "", # Leave empty if it's a personal project, otherwise put the Org Name
        "board_id": 10,
        "record_date": "2026-07-12",
        "start_date": "2026-07-01",
        "end_date": "2026-07-12",
        "kpi_config": {"total_ideal_points": 100.0},
        
        # We leave raw_json EMPTY because we want S0 to fetch it live!
        "raw_json": {}, 
        
        # Simulate empty historical data (starts fresh)
        "orchestrator_data_od": [], 
        
        "output_format": "csv" # We want a CSV dump for Excel
    }

    print(f"Executing Live Pipeline for {GITHUB_REPO} Project #{PROJECT_NUMBER}...")
    
    # 2. Run the Factory (S0 -> S1 -> S2 -> S3)
    result = AnalyticsWorkerFactory.execute(payload)

    # 3. Dump the result to a CSV
    csv_content = result.get("graphic_contract", "")
    output_path = os.path.abspath("live_dashboard_data.csv")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
        
    print(f"Success! Live data dumped to {output_path}")

if __name__ == "__main__":
    main()
