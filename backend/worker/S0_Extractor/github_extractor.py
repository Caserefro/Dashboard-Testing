"""
GitHub Projects & Repos API Extractor (`backend/extractors/github_extractor.py`)

Invoked Process Architecture (`sys.stdin -> sys.stdout` Pure Factory pattern).
Receives extraction requirements via `sys.stdin`:
  `{ "board_id": int, "api_key": str, "missing_dates": List[str], "repo": str }`

Executes GitHub GraphQL/REST retrieval (`or clean dummy simulation locally`) and outputs 100% Raw Vendor JSON via `sys.stdout`:
  `{ "workItems": [...], "pullRequests": [...], "repo": str }`
"""

import sys
import json
from typing import Dict, Any, List


class GitHubProjectsExtractor:
    """Invoked process entity responsible for fetching GitHub Projects V2 (workItems) and Repos (pullRequests)."""

    @classmethod
    def execute(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes GitHub API extraction.
        Currently populated with high-fidelity dummy data matching GitHub REST/GraphQL structures
        so live HTTP calls (`httpx.get / post`) can be dropped in cleanly from the company machine.
        """
        board_id = int(payload.get("board_id", 20))
        api_key = payload.get("api_key", "")
        missing_dates: List[str] = payload.get("missing_dates", [])
        repo = payload.get("repo", "owner/github-repo")

        work_items: List[Dict[str, Any]] = []
        pull_requests: List[Dict[str, Any]] = []

        for idx, date_str in enumerate(missing_dates):
            issue_num = 100 + idx
            pr_num = 200 + idx

            # Simulated GitHub Project Issue / Item
            work_items.append({
                "id": f"GH-{issue_num}",
                "number": issue_num,
                "fields": {
                    "System.WorkItemType": "Feature" if idx % 2 == 0 else "Bug",
                    "System.State": "closed",
                    "story_points": 8.0 if idx % 2 == 0 else 3.0,
                    "System.CreatedDate": f"{date_str}T08:30:00Z",
                    "completed_date": f"{date_str}T16:45:00Z",
                    "title": f"GitHub Issue #{issue_num} for {repo}"
                }
            })

            # Simulated GitHub Pull Request
            pull_requests.append({
                "pullRequestId": pr_num,
                "title": f"Fix/Feature PR #{pr_num}",
                "status": "closed",
                "creationDate": f"{date_str}T11:00:00Z",
                "commentCount": 1 if idx % 2 != 0 else 0,
                "commitsAfterCreation": 2 if idx % 2 != 0 else 0
            })

        return {
            "workItems": work_items,
            "pullRequests": pull_requests,
            "repo": repo,
            "cutoff": missing_dates[0] if missing_dates else "2026-04-01T00:00:00Z"
        }


def main() -> None:
    """Main entrypoint when invoked via `python -m backend.extractors.github_extractor` or inside Docker container."""
    try:
        input_data = sys.stdin.read()
        payload = json.loads(input_data) if input_data.strip() else {}

        output = GitHubProjectsExtractor.execute(payload)

        sys.stdout.write(json.dumps(output, indent=2))
        sys.stdout.flush()
        sys.exit(0)
    except Exception as e:
        error = {"error": "GitHubProjectsExtractorExecutionError", "details": str(e)}
        sys.stderr.write(json.dumps(error) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
