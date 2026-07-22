"""
Live GitHub Runner for Spreadsheet API
"""

import sys
import json
import os
from backend.worker.S0_Extractor.github.github_extractor import GitHubExtractor
from backend.worker.worker_factory import AnalyticsWorkerFactory

def main():
    REAL_GITHUB_PAT = "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"
    GITHUB_REPO = "Caserefro/TestRepo"
    PROJECT_NUMBER = 2

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
        "output_format": "spreadsheet",
        "debug_mode": True
    })

    # Save JSON contract
    output_path = os.path.abspath("live_dashboard_spreadsheet.json")
    with open(output_path, "w", encoding="utf-8") as f:
        # result["graphic_contract"] is a dict for spreadsheet, or JSON str depending on Formatter
        if isinstance(result.get("graphic_contract"), dict):
            json.dump(result["graphic_contract"], f, indent=2)
        else:
            # Maybe it's a string from json.dumps
            try:
                parsed = json.loads(result.get("graphic_contract", "{}"))
                json.dump(parsed, f, indent=2)
            except Exception:
                f.write(str(result.get("graphic_contract", "")))
                
    print(f"Success! Saved to {output_path}")

if __name__ == "__main__":
    main()
