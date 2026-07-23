"""
Live GitHub Runner (`run_live_github.py`)

Dumb runner script. No business logic.
Just passes credentials to S0 Extractor, feeds the output to the Factory, and saves the result.
"""

import sys
import os
import json

# Add the project root to sys.path so we can import 'backend'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.worker.S0_Extractor.github.github_extractor import GitHubExtractor
from backend.worker.worker_factory import AnalyticsWorkerFactory

def main():
    REAL_GITHUB_PAT = "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"
    GITHUB_REPO = "Caserefro/TestRepo"
    PROJECT_NUMBER = 2

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
        "missing_dates": [],
        "ssl_verify": False
    })
    print(f"Extracted {len(raw_json.get('workItems', []))} issues, {len(raw_json.get('pullRequests', []))} PRs.")

    record_date = "2026-07-22"  # Update to today's date for accurate writing!
    do_backfill = "--backfill" in sys.argv

    # S1 -> S2 -> S3: Factory handles everything (sprint detection, math, formatting)
    result = AnalyticsWorkerFactory.execute({
        "board_id": 10,
        "record_date": record_date,
        "raw_json": raw_json,
        "orchestrator_data_od": [],
        "output_format": "csv",
        "debug_mode": True,
        "backfill": do_backfill
    })

    # Save CSV
    csv_content = result.get("graphic_contract", "")
    output_path = os.path.join(os.path.dirname(__file__), "live_dashboard_output_v2.csv")
    output_path = os.path.abspath(output_path)
    
    if do_backfill:
        # Backfill Engine generated the perfect stateful CSV directly!
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            f.write(csv_content)
    else:
        # Use Temporal Publisher for daily incremental writes
        from backend.publisher.temporal_csv_publisher import TemporalCsvPublisher
        TemporalCsvPublisher.publish(csv_content, record_date, output_path)
        
    print(f"Success! Saved to {output_path}")

if __name__ == "__main__":
    main()
