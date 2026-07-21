"""
Stage 1: Normalizer (`s1_normalizer.py`)

Receives `Raw Json + OD` from the Orchestrator, scrubs messy vendor payloads (Azure DevOps & GitHub Projects),
traps anomalies/human entry typos (`"TBD"` in numeric fields, null dates), and returns clean, canonical
`NormalizedTicket` records in RAM with zero unnecessary serialization copies.
"""

from typing import List, Dict, Any, Tuple
from backend.domain.process_data_models import NormalizedTicket

from .mappers.azure_mapper import AzureMapper
from .mappers.github_mapper import GitHubMapper

class Normalizer:
    """Stage 1: Normalizer entity. Transforms raw vendor payloads and historical OD into canonical Process Data."""

    @classmethod
    def _get_mapper(cls, raw_json: Dict[str, Any], board_id: int):
        """Detects the payload source and returns the appropriate mapper strategy."""
        work_items = raw_json.get("workItems", raw_json.get("value", []))
        if not work_items and "sampleItems" in raw_json:
            work_items = raw_json["sampleItems"]
            
        if work_items:
            first_item = work_items[0]
            fields = first_item.get("fields", first_item)
            # Azure DevOps uses System.* namespaced keys
            if "System.WorkItemType" in fields or "System.State" in fields:
                return AzureMapper
            # GitHub uses fieldValues array with fieldName keys
            if "fieldValues" in first_item or "type" in fields or "projectItemType" in first_item:
                return GitHubMapper
                
        # Fallback: check PR shape for Azure-specific format
        pull_requests = raw_json.get("pullRequests", raw_json.get("pull_requests", []))
        if pull_requests:
            first_pr = pull_requests[0]
            # Azure PRs have nested reviewers, completionOptions, etc.
            if "reviewers" in first_pr or "completionOptions" in first_pr:
                return AzureMapper
            return GitHubMapper
                
        # Ultimate fallback
        if board_id == 10:
            return GitHubMapper
        return AzureMapper

    @classmethod
    def normalize_raw_json(cls, raw_json: Dict[str, Any], board_id: int, default_record_date: str) -> List[NormalizedTicket]:
        """
        Scrubs 100% Raw JSON dumped by Azure API / GitHub API into canonical NormalizedTicket instances.
        Delegates mapping to the vendor-specific strategy.
        """
        mapper = cls._get_mapper(raw_json, board_id)
        
        tickets: List[NormalizedTicket] = []
        work_items = raw_json.get("workItems", raw_json.get("value", []))
        if not work_items and "sampleItems" in raw_json:
            work_items = raw_json["sampleItems"]

        for item in work_items:
            try:
                ticket = mapper.map_ticket(item, board_id, default_record_date)
                tickets.append(ticket)
            except Exception as e:
                # In production we might log this or skip the corrupt record
                pass

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
        Scrubs exact PR packages and delegates to the vendor-specific strategy.
        """
        mapper = cls._get_mapper(raw_json, board_id)
        repo_name = str(raw_json.get("repo", "UNKNOWN"))
        
        prs = []
        pull_requests = raw_json.get("pullRequests", raw_json.get("pull_requests", []))

        for item in pull_requests:
            try:
                pr = mapper.map_pr(item, board_id, repo_name, default_record_date)
                prs.append(pr)
            except Exception as e:
                pass

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
