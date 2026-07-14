"""
Stage 1: Normalizer (`s1_normalizer.py`)

Receives `Raw Json + OD` from the Orchestrator, scrubs messy vendor payloads (Azure DevOps & GitHub Projects),
traps anomalies/human entry typos (`"TBD"` in numeric fields, null dates), and returns clean, canonical
`NormalizedTicket` records in RAM with zero unnecessary serialization copies.
"""

from typing import List, Dict, Any, Tuple
from backend.models.process_data_models import NormalizedTicket


class Normalizer:
    """Stage 1: Normalizer entity. Transforms raw vendor payloads and historical OD into canonical Process Data."""

    @staticmethod
    def _parse_story_points(raw_val: Any) -> float:
        """Safely converts raw story point entry into a float. Handles typos ('TBD', None, empty strings)."""
        if raw_val is None or raw_val == "":
            return 0.0
        try:
            return float(raw_val)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _normalize_unit_type(raw_type: str) -> str:
        """Maps vendor-specific work item types to canonical unit_type."""
        upper = raw_type.upper()
        if "STORY" in upper or "FEATURE" in upper:
            return "USER_STORY"
        elif "BUG" in upper:
            return "BUG"
        return "TASK"

    @staticmethod
    def _normalize_status(raw_status: str) -> str:
        """Maps vendor-specific statuses to canonical status_normalized."""
        upper = raw_status.upper()
        if upper in ("DONE", "CLOSED", "RESOLVED", "MERGED"):
            return "DONE"
        elif upper in ("IN PROGRESS", "DOING", "ACTIVE"):
            return "IN_PROGRESS"
        elif upper in ("CANCELLED", "REJECTED", "REMOVED"):
            return "CANCELLED"
        return "TODO"

    @classmethod
    def normalize_raw_json(cls, raw_json: Dict[str, Any], board_id: int, default_record_date: str) -> List[NormalizedTicket]:
        """
        Scrubs 100% Raw JSON dumped by Azure API / GitHub API into canonical NormalizedTicket instances.
        """
        tickets: List[NormalizedTicket] = []
        work_items = raw_json.get("workItems", raw_json.get("value", []))

        for item in work_items:
            fields = item.get("fields", item)
            ticket_id = str(item.get("id", fields.get("System.Id", "UNKNOWN")))

            # Multi-vendor Type detection: checks Azure `System.WorkItemType` then GitHub/Jira `type` or labels
            unit_type_raw = fields.get("System.WorkItemType", fields.get("type", "Task"))
            unit_type = cls._normalize_unit_type(unit_type_raw)

            # Multi-vendor State detection: checks Azure `System.State` then GitHub `state` (`closed`/`open`)
            status_raw = fields.get("System.State", fields.get("state", item.get("state", "To Do")))
            status_norm = cls._normalize_status(status_raw)

            # Multi-vendor Story Points: checks Azure `Microsoft.VSTS.Scheduling.StoryPoints` then GitHub/custom `story_points`
            story_points = cls._parse_story_points(
                fields.get("Microsoft.VSTS.Scheduling.StoryPoints", fields.get("story_points", item.get("story_points", 0)))
            )

            # Multi-vendor Created Date: checks Azure `System.CreatedDate` then GitHub `created_at`
            created_raw = fields.get("System.CreatedDate", fields.get("created_at", item.get("created_at", default_record_date)))
            created_date = str(created_raw)[:10]

            # Multi-vendor Closed Date: checks Azure `ClosedDate` then GitHub `closed_at` / `completed_date`
            completed_date_raw = fields.get("Microsoft.VSTS.Common.ClosedDate", fields.get("closed_at", fields.get("completed_date", item.get("closed_at"))))
            if completed_date_raw:
                completed_date = str(completed_date_raw)[:10]
            else:
                completed_date = (default_record_date if status_norm == "DONE" else None)

            # FTY: clean completion with zero reopen/rejection loops
            reopen_count = int(cls._parse_story_points(
                fields.get("Microsoft.VSTS.Common.StateChangeDate_Reopened", 0)
            ))
            is_fty = (status_norm == "DONE" and reopen_count == 0)

            tickets.append(NormalizedTicket(
                ticket_id=ticket_id,
                unit_type=unit_type,
                status_normalized=status_norm,
                story_points=story_points,
                created_date=created_date,
                completed_date=completed_date,
                is_first_time_yield=is_fty,
                board_id=board_id,
                comments=fields.get("System.Title", fields.get("title", item.get("title", "")))
            ))

        return tickets

    @classmethod
    def normalize_db_od(cls, orchestrator_data_od: List[Dict[str, Any]]) -> List[NormalizedTicket]:
        """
        Deserializes historical DB Process Data (OD) directly into fast Python references.
        """
        tickets: List[NormalizedTicket] = []
        for item in orchestrator_data_od:
            try:
                tickets.append(NormalizedTicket.from_dict(item))
            except Exception:
                continue
        return tickets

    @classmethod
    def normalize_prs(cls, raw_json: Dict[str, Any], board_id: int, default_record_date: str) -> List[Any]:
        """
        Scrubs exact Azure DevOps pullRequests package (`pullRequestId`, `status`, `creationDate`, `commentCount`, `commitsAfterCreation`)
        and GitHub PR payloads into canonical NormalizedPR instances.
        """
        from backend.models.process_data_models import NormalizedPR

        prs: List[NormalizedPR] = []
        pull_requests = raw_json.get("pullRequests", raw_json.get("pull_requests", []))
        repo_name = str(raw_json.get("repo", "UNKNOWN"))

        for item in pull_requests:
            pr_id = str(item.get("pullRequestId", item.get("id", item.get("number", "UNKNOWN"))))
            title = str(item.get("title", ""))
            
            # Multi-vendor PR status: Azure (`active`/`completed`) vs GitHub (`open`/`closed`/`merged`)
            status_raw = str(item.get("status", item.get("state", "active"))).upper()

            if status_raw in ("COMPLETED", "MERGED", "CLOSED"):
                status_norm = "MERGED" if status_raw != "ABANDONED" else "CLOSED"
            elif status_raw in ("ABANDONED", "CANCELLED", "REJECTED"):
                status_norm = "CLOSED"
            else:
                status_norm = "OPEN"

            created_date_raw = str(item.get("creationDate", item.get("created_at", default_record_date)))[:10]
            merged_date = created_date_raw if status_norm == "MERGED" else None

            comment_count = int(item.get("commentCount", item.get("comments", 0)))
            commits_after = int(item.get("commitsAfterCreation", item.get("review_commits", 0)))

            prs.append(NormalizedPR(
                pr_id=pr_id,
                title=title,
                repository=repo_name,
                status_normalized=status_norm,
                lines_added=0,
                lines_removed=0,
                created_date=created_date_raw,
                merged_date=merged_date,
                board_id=board_id,
                comment_count=comment_count,
                commits_after_creation=commits_after
            ))

        return prs

    @classmethod
    def normalize_all(
        cls,
        raw_json: Dict[str, Any],
        orchestrator_data_od: List[Dict[str, Any]],
        board_id: int,
        record_date: str
    ) -> Tuple[List[NormalizedTicket], List[NormalizedTicket], List[Any]]:
        """
        Master Normalizer entrypoint. Returns `(new_tickets, old_tickets, new_prs)` cleanly in RAM.
        Zero memory copy: pointer lists are concatenated directly by caller `O(1)`.
        """
        new_tickets = cls.normalize_raw_json(raw_json, board_id, record_date)
        old_tickets = cls.normalize_db_od(orchestrator_data_od)
        new_prs = cls.normalize_prs(raw_json, board_id, record_date)
        return new_tickets, old_tickets, new_prs
