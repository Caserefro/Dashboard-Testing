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

            unit_type = cls._normalize_unit_type(fields.get("System.WorkItemType", "Task"))
            status_norm = cls._normalize_status(fields.get("System.State", "To Do"))

            story_points = cls._parse_story_points(
                fields.get("Microsoft.VSTS.Scheduling.StoryPoints", fields.get("story_points", 0))
            )

            created_date = str(fields.get("System.CreatedDate", default_record_date))[:10]

            completed_date_raw = fields.get("Microsoft.VSTS.Common.ClosedDate", fields.get("completed_date"))
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
                comments=fields.get("System.Title", fields.get("title", ""))
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
    def normalize_all(
        cls,
        raw_json: Dict[str, Any],
        orchestrator_data_od: List[Dict[str, Any]],
        board_id: int,
        record_date: str
    ) -> Tuple[List[NormalizedTicket], List[NormalizedTicket]]:
        """
        Master Normalizer entrypoint. Returns `(new_tickets, old_tickets)` cleanly in RAM.
        Zero memory copy: pointer lists are concatenated directly by caller `O(1)`.
        """
        new_tickets = cls.normalize_raw_json(raw_json, board_id, record_date)
        old_tickets = cls.normalize_db_od(orchestrator_data_od)
        return new_tickets, old_tickets
