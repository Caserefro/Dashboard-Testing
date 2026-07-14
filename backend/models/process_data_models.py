"""
Canonical Process Data Models for the Daily Management System (DMS).

As defined in the Miro architecture:
The Normalizer scrubs raw vendor data (Azure DevOps, GitHub Projects) into these clean
canonical data structures (`Tickets`, `Issues`, `PRs`, `Story Points`).

These records are:
1. Passed in RAM to the `Analizer` to compute First Time Yield, Burndown, and Velocity.
2. Returned as `KPI_Record for DB` to be persisted inside Postgres (`KPI_RECORDS_DAILY.process_data_json`).
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class NormalizedTicket:
    """Represents a clean, normalized work item / ticket (User Story, Bug, Task)."""
    ticket_id: str                  # e.g., "AZ-1042" or "GH-301"
    unit_type: str                  # e.g., "USER_STORY", "BUG", "TASK"
    status_normalized: str          # e.g., "TODO", "IN_PROGRESS", "DONE", "CANCELLED"
    story_points: float             # e.g., 5.0 (0.0 if unassigned or invalid)
    created_date: str               # ISO-8601 date string YYYY-MM-DD
    completed_date: Optional[str]   # ISO-8601 date string YYYY-MM-DD if completed, else None
    is_first_time_yield: bool       # True if completed without reopening/rejection loops
    board_id: int                   # FK to BOARDS.board_id
    comments: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedTicket":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NormalizedPR:
    """Represents a clean, normalized code Pull Request."""
    pr_id: str                      # e.g., "PR-88"
    title: str                      # PR title
    repository: str                 # Repository name
    status_normalized: str          # e.g., "OPEN", "MERGED", "CLOSED"
    lines_added: int
    lines_removed: int
    created_date: str               # ISO-8601 date string YYYY-MM-DD
    merged_date: Optional[str]      # ISO-8601 date string YYYY-MM-DD if merged, else None
    board_id: int                   # FK to BOARDS.board_id

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedPR":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NormalizedIssue:
    """Represents a clean, normalized Pareto or Safety/Operational issue."""
    issue_id: str                   # e.g., "ISSUE-12"
    category: str                   # e.g., "Safety", "Quality", "Delivery", "Cost", "Morale"
    status: str                     # e.g., "OPEN", "RESOLVED"
    severity: int                   # 1 (Critical) to 5 (Minor)
    event_ts: str                   # ISO-8601 timestamp YYYY-MM-DDTHH:MM:SS
    board_id: int                   # FK to BOARDS.board_id
    description: str = ""
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedIssue":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProcessDataBundle:
    """
    Holds the complete set of canonical facts for a specific board and time window.
    This bundle is what gets serialized into `KPI_RECORDS_DAILY.process_data_json`.
    """
    board_id: int
    record_date: str                # ISO-8601 date string YYYY-MM-DD
    tickets: List[NormalizedTicket] = field(default_factory=list)
    prs: List[NormalizedPR] = field(default_factory=list)
    issues: List[NormalizedIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_id": self.board_id,
            "record_date": self.record_date,
            "tickets": [t.to_dict() for t in self.tickets],
            "prs": [p.to_dict() for p in self.prs],
            "issues": [i.to_dict() for i in self.issues],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessDataBundle":
        tickets = [NormalizedTicket.from_dict(t) for t in data.get("tickets", [])]
        prs = [NormalizedPR.from_dict(p) for p in data.get("prs", [])]
        issues = [NormalizedIssue.from_dict(i) for i in data.get("issues", [])]
        return cls(
            board_id=data.get("board_id", 0),
            record_date=data.get("record_date", ""),
            tickets=tickets,
            prs=prs,
            issues=issues,
        )


@dataclass
class ProcessDataAggregate:
    """
    Lightweight Daily Aggregated Process Data (~300 bytes).
    This aggregate summary is the optimal payload written to `KPI_RECORDS_DAILY.process_data_json`
    (`KPI_Record for DB`) to ensure microscopic storage and sub-millisecond chart interpretation.
    """
    board_id: int
    record_date: str
    total_story_points: float = 0.0
    completed_story_points: float = 0.0
    remaining_story_points: float = 0.0
    total_completed_tickets: int = 0
    first_time_yield_clean_tickets: int = 0
    prs_merged_count: int = 0
    safety_issues_open_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessDataAggregate":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def create_from_items(
        cls,
        board_id: int,
        record_date: str,
        tickets: List[NormalizedTicket],
        prs: List[NormalizedPR],
        issues: List[NormalizedIssue],
        total_ideal_points: Optional[float] = None
    ) -> "ProcessDataAggregate":
        total_pts = total_ideal_points if (total_ideal_points and total_ideal_points > 0) else sum(t.story_points for t in tickets)
        completed_pts = sum(t.story_points for t in tickets if t.status_normalized == "DONE" and (not t.completed_date or t.completed_date <= record_date[:10]))
        remaining_pts = max(0.0, total_pts - completed_pts)
        completed_tix = [t for t in tickets if t.status_normalized == "DONE" and (not t.completed_date or t.completed_date <= record_date[:10])]
        fty_clean = sum(1 for t in completed_tix if t.is_first_time_yield)
        prs_merged = sum(1 for p in prs if p.status_normalized == "MERGED" and (not p.merged_date or p.merged_date <= record_date[:10]))
        safety_open = sum(1 for i in issues if i.status == "OPEN" and i.category.lower() == "safety")

        return cls(
            board_id=board_id,
            record_date=record_date[:10],
            total_story_points=round(total_pts, 2),
            completed_story_points=round(completed_pts, 2),
            remaining_story_points=round(remaining_pts, 2),
            total_completed_tickets=len(completed_tix),
            first_time_yield_clean_tickets=fty_clean,
            prs_merged_count=prs_merged,
            safety_issues_open_count=safety_open
        )

