from typing import Dict, Any
from backend.domain.process_data_models import NormalizedTicket, NormalizedPR
from .base_mapper import BaseMapper

class GitHubMapper(BaseMapper):
    """Maps GitHub Projects V2 payloads into Process Data objects."""

    @classmethod
    def map_ticket(cls, item: Dict[str, Any], board_id: int, default_record_date: str) -> NormalizedTicket:
        fields = item.copy()
        sprint_name = None
        
        # Merge fieldValues directly
        gh_fields = {}
        if "populatedFields" in item:
            gh_fields = {f["fieldName"]: f.get("value") for f in item["populatedFields"]}
        elif "content" in item and "fieldValues" in item["content"]:
            gh_fields = {f["fieldName"]: f.get("value") for f in item["content"]["fieldValues"]}
        elif "fieldValues" in item:
            gh_fields = {f["fieldName"]: f.get("value") for f in item["fieldValues"] if isinstance(f, dict)}
            
        if gh_fields:
            if "content" in item:
                fields.update(item["content"])
            fields.update(gh_fields)
            fields["id"] = item.get("id", fields.get("id"))
            fields["type"] = item.get("type", item.get("projectItemType", "Issue"))
            sprint_name = gh_fields.get("Sprint")

        ticket_id = str(fields.get("id", "UNKNOWN"))
        unit_type = cls.normalize_unit_type(fields.get("type", "Task"))
        
        status_raw = fields.get("Status", fields.get("state", "To Do"))
        status_norm = cls.normalize_status(status_raw)
        
        story_points = cls.parse_story_points(fields.get("Estimate", fields.get("story_points", 0)))
        
        created_raw = fields.get("created_at", fields.get("createdAt", default_record_date))
        created_date = str(created_raw)[:10]
        
        completed_date_raw = fields.get("closed_at", fields.get("completed_date"))
        if completed_date_raw:
            completed_date = str(completed_date_raw)[:10]
        else:
            completed_date = (default_record_date if status_norm == "DONE" else None)
            
        rework_loops = item.get("rework_loops", 0)
        time_in_todo_sec = float(item.get("time_in_todo_sec", 0.0))
        time_in_progress_sec = float(item.get("time_in_progress_sec", 0.0))
        time_in_review_sec = float(item.get("time_in_review_sec", 0.0))
        
        labels = item.get("labels", [])
        is_bug = any("bug" in str(l).lower() for l in labels) if labels else (unit_type == "BUG")

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
            sprint=sprint_name,
            comments=fields.get("title", ""),
            rework_loops=rework_loops,
            time_in_todo_sec=time_in_todo_sec,
            time_in_progress_sec=time_in_progress_sec,
            time_in_review_sec=time_in_review_sec,
            is_bug=is_bug,
            estimate=story_points
        )

    @classmethod
    def map_pr(cls, item: Dict[str, Any], board_id: int, repo_name: str, default_record_date: str) -> NormalizedPR:
        pr_id = str(item.get("id", item.get("number", "UNKNOWN")))
        title = str(item.get("title", ""))
        
        status_raw = str(item.get("state", item.get("status", "open"))).upper()
        if status_raw in ("MERGED", "CLOSED"):
            status_norm = "MERGED" if status_raw == "MERGED" else "CLOSED"
        else:
            status_norm = "OPEN"
            
        created_date_raw = str(item.get("created_at", item.get("creationDate", default_record_date)))[:10]
        merged_date = created_date_raw if status_norm == "MERGED" else None
        
        comment_count = int(item.get("comments", item.get("commentCount", 0)))
        commits_after = int(item.get("review_commits", item.get("commitsAfterCreation", 0)))
        review_cycles = int(item.get("review_cycles", 0))

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
            review_cycles=review_cycles
        )
