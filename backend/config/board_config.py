"""
Centralized Configuration for Project ATLAS Board Adaptation (`backend/config/board_config.py`)

Modify STATUS_MAP and ESTIMATE_BUCKET_CONFIG here to quickly adapt Project ATLAS
to any team's project board statuses and estimate schemes.
"""

from typing import Dict, Any, Tuple

# Prominent Status Map (Maps raw vendor status strings to canonical stage names)
STATUS_MAP: Dict[str, str] = {
    "todo": "Todo",
    "to do": "Todo",
    "backlog": "Todo",
    "in progress": "InProgress",
    "doing": "InProgress",
    "active": "InProgress",
    "in review": "InReview",
    "review": "InReview",
    "dev testing": "DevTesting",
    "dev_testing": "DevTesting",
    "testing": "DevTesting",
    "done": "Done",
    "closed": "Done"
}

# Configurable Estimate Bucket Definition
# MODE options:
#   - "RAW": Outputs exact raw numeric estimate keys (E1, E2, E3, E4, E5, E6, etc.)
#   - "BUCKETED": Maps numeric estimates into the defined ranges below
ESTIMATE_BUCKET_CONFIG: Dict[str, Any] = {
    "MODE": "RAW",  # Change to "BUCKETED" to combine numeric estimates into ranges
    "RANGES": {
        "E2": (0.0, 3.0),
        "E4": (3.0, 6.0),
        "E8": (6.0, 12.0),
        "E16": (12.0, 999.0)
    }
}
