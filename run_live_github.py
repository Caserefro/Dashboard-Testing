"""
Live GitHub Runner (`run_live_github.py`)

Dumb runner script. No business logic.
Just passes credentials to S0 Extractor, feeds the output to the Factory, and saves the result.
"""

import sys
import json
import os
from backend.worker.S0_Extractor.github.github_extractor import GitHubExtractor
from backend.worker.worker_factory import AnalyticsWorkerFactory

def main():
    REAL_GITHUB_PAT = "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"
    GITHUB_REPO = "Caserefro/Dashboard-Testing"
    PROJECT_NUMBER = 1

    if REAL_GITHUB_PAT == "ghp_your_actual_token_here":
        print("ERROR: Please insert your real GitHub PAT!")
        sys.exit(1)

    # S0: Extract
    print(f"Extracting from {GITHUB_REPO} Project #{PROJECT_NUMBER}...")
    raw_json = GitHubExtractor.execute({
        "api_key": REAL_GITHUB_PAT,
        "repo": GITHUB_REPO,
        "projectNumber": PROJECT_NUMBER,
        "org": "",
        "missing_dates": []
    })
    print(f"Extracted {len(raw_json.get('workItems', []))} issues, {len(raw_json.get('pullRequests', []))} PRs.")

    # S1 -> S2 -> S3: Factory handles everything (sprint detection, math, formatting)
    result = AnalyticsWorkerFactory.execute({
        "board_id": 10,
        "record_date": "2026-07-21",
        "raw_json": raw_json,
        "orchestrator_data_od": [],
        "output_format": "csv",
        "debug_mode": True
    })

    # Save CSV
    csv_content = result.get("graphic_contract", "")
    output_path = os.path.abspath("live_dashboard_output.csv")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    print(f"Success! Saved to {output_path}")

if __name__ == "__main__":
    main()
