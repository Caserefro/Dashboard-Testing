"""
Azure DevOps API Extractor (`backend/extractors/azure_extractor.py`)

Invoked Process Architecture (`sys.stdin -> sys.stdout` Pure Factory pattern).
Receives extraction requirements via `sys.stdin`:
  `{ "board_id": int, "api_key": str, "missing_dates": List[str], "team": str, "repo": str }`

Executes data retrieval (`or clean dummy simulation locally`) and outputs 100% Raw Vendor JSON via `sys.stdout`:
  `{ "workItems": [...], "pullRequests": [...], "repo": str }`
"""

import sys
import json
from typing import Dict, Any, List


class AzureDevOpsExtractor:
    """Invoked process entity responsible for fetching Azure Boards (workItems) and Repos (pullRequests)."""

    @classmethod
    def execute(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes Azure API extraction.
        Currently populated with high-fidelity dummy data matching our exact screenshot packages so that
        the exact live HTTP requests (`httpx.get`) can be dropped in cleanly from the company machine.
        """
        board_id = int(payload.get("board_id", 10))
        api_key = payload.get("api_key", "")
        missing_dates: List[str] = payload.get("missing_dates", [])
        team = payload.get("team", "smth")
        repo = payload.get("repo", "Team")

        work_items: List[Dict[str, Any]] = []
        pull_requests: List[Dict[str, Any]] = []

        # Generate simulated items for every missing date in the gap
        for idx, date_str in enumerate(missing_dates):
            ticket_id = f"AZ-{board_id * 100 + idx}"
            pr_id = 500 + (board_id * 10) + idx

            # Simulated Azure Board Work Item
            work_items.append({
                "id": ticket_id,
                "fields": {
                    "System.WorkItemType": "User Story" if idx % 2 == 0 else "Bug",
                    "System.State": "Done",
                    "Microsoft.VSTS.Scheduling.StoryPoints": 5.0 if idx % 2 == 0 else "TBD",
                    "System.CreatedDate": f"{date_str}T09:00:00.0000000Z",
                    "Microsoft.VSTS.Common.ClosedDate": f"{date_str}T17:00:00.0000000Z",
                    "System.Title": f"Task/Story {ticket_id} for Board {board_id}"
                }
            })

            # Simulated Azure Repos Pull Request matching exact screenshot package
            pull_requests.append({
                "pullRequestId": pr_id,
                "title": f"Task{pr_id}",
                "status": "active" if idx == 0 else "completed",
                "creationDate": f"{date_str}T16:35:06.1245666Z",
                "commentCount": 0,
                "commitsAfterCreation": 1 if idx % 2 == 0 else 0
            })

        return {
            "workItems": work_items,
            "pullRequests": pull_requests,
            "team": team,
            "repo": repo,
            "cutoff": missing_dates[0] if missing_dates else "2026-04-01T00:00:00+00:00"
        }


def main() -> None:
    """Main entrypoint when invoked via `python -m backend.extractors.azure_extractor` or inside Docker container."""
    try:
        input_data = sys.stdin.read()
        payload = json.loads(input_data) if input_data.strip() else {}

        output = AzureDevOpsExtractor.execute(payload)

        sys.stdout.write(json.dumps(output, indent=2))
        sys.stdout.flush()
        sys.exit(0)
    except Exception as e:
        error = {"error": "AzureDevOpsExtractorExecutionError", "details": str(e)}
        sys.stderr.write(json.dumps(error) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
