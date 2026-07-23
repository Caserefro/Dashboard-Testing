from typing import Dict, Any
from backend.domain.process_data_models import NormalizedTicket, NormalizedPR
from .base_mapper import BaseMapper

class AzureMapper(BaseMapper):
    """Maps Azure DevOps payloads into Process Data objects."""

    @classmethod
    def map_ticket(cls, item: Dict[str, Any], board_id: int, default_record_date: str) -> NormalizedTicket:
        fields = item.get("fields", item)
        ticket_id = str(item.get("id", fields.get("System.Id", "UNKNOWN")))
        
        unit_type_raw = fields.get("System.WorkItemType", "Task")
        unit_type = cls.normalize_unit_type(unit_type_raw)
        
        status_raw = fields.get("System.State", "To Do")
        status_norm = cls.normalize_status(status_raw)
        
        story_points = cls.parse_story_points(fields.get("Microsoft.VSTS.Scheduling.StoryPoints", 0))
        
        created_raw = fields.get("System.CreatedDate", default_record_date)
        created_date = str(created_raw)[:10]
        
        completed_date_raw = fields.get("Microsoft.VSTS.Common.ClosedDate")
        if completed_date_raw:
            completed_date = str(completed_date_raw)[:10]
        else:
            completed_date = (default_record_date if status_norm == "DONE" else None)
            
        reopen_count = int(cls.parse_story_points(fields.get("Microsoft.VSTS.Common.StateChangeDate_Reopened", 0)))
        rework_loops = reopen_count
        
        is_bug = (unit_type == "BUG")
        is_fty = (status_norm == "DONE" and rework_loops == 0)

        return NormalizedTicket(
            ticket_id=ticket_id,
            unit_type=unit_type,
            status_normalized=status_norm,
            story_points=story_points,
            created_date=created_date,
            completed_date=completed_date,
            is_first_time_yield=is_fty,
            board_id=board_id,
            sprint=None,
            comments=fields.get("System.Title", ""),
            rework_loops=rework_loops,
            time_in_todo_sec=0.0,
            time_in_progress_sec=0.0,
            time_in_review_sec=0.0,
            is_bug=is_bug,
            estimate=story_points
        )

    @classmethod
    def map_pr(cls, item: Dict[str, Any], board_id: int, repo_name: str, default_record_date: str) -> NormalizedPR:
        pr_id = str(item.get("pullRequestId", "UNKNOWN"))
        title = str(item.get("title", ""))
        
        status_raw = str(item.get("status", "active")).upper()
        if status_raw in ("COMPLETED", "MERGED", "CLOSED"):
            status_norm = "MERGED" if status_raw != "ABANDONED" else "CLOSED"
        elif status_raw in ("ABANDONED", "CANCELLED", "REJECTED"):
            status_norm = "CLOSED"
        else:
            status_norm = "OPEN"
            
        created_date_raw = str(item.get("creationDate", default_record_date))[:10]
        merged_date = created_date_raw if status_norm == "MERGED" else None
        
        comment_count = int(item.get("commentCount", 0))
        commits_after = int(item.get("commitsAfterCreation", 0))

        return NormalizedPR(
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
            commits_after_creation=commits_after,
            review_cycles=0
        )
