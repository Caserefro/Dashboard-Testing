"""
Stage 0 / Stage 1 Status Mapping Configuration (`backend/worker/S0_Extractor/github/status_config.py`)

Single Responsibility: Defines vendor status string translations into canonical stage names.
"""

from typing import Dict

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
