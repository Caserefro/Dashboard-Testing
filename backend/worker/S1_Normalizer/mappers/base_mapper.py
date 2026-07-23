from typing import Any

class BaseMapper:
    """Base class for all vendor-specific data mappers."""

    @staticmethod
    def parse_story_points(raw_val: Any) -> float:
        """Safely converts raw story point entry into a float. Handles typos ('TBD', None, empty strings)."""
        if raw_val is None or raw_val == "":
            return 0.0
        try:
            return float(raw_val)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def normalize_unit_type(raw_type: str) -> str:
        """Maps vendor-specific work item types to canonical unit_type."""
        upper = raw_type.upper() if raw_type else ""
        if "STORY" in upper or "FEATURE" in upper:
            return "USER_STORY"
        elif "BUG" in upper:
            return "BUG"
        return "TASK"

    @staticmethod
    def normalize_status(raw_status: str) -> str:
        """Maps vendor-specific statuses to canonical status_normalized."""
        upper = raw_status.upper() if raw_status else ""
        if upper in ("DONE", "CLOSED", "RESOLVED", "MERGED"):
            return "DONE"
        elif upper in ("IN PROGRESS", "DOING", "ACTIVE"):
            return "IN_PROGRESS"
        elif upper in ("IN REVIEW", "REVIEW", "IN_REVIEW", "DEV TESTING", "DEV_TESTING"):
            return "IN_REVIEW"
        elif upper in ("CANCELLED", "REJECTED", "REMOVED"):
            return "CANCELLED"
        return "TODO"
