"""
Stage 0 GitHub Extractor Configuration (`backend/worker/S0_Extractor/github/extractor_config.py`)

Encapsulates all GitHub Extractor settings: vendor status translations, SSL verify defaults, and GraphQL query timeouts.
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

GRAPHQL_TIMEOUT_SEC: float = 5.0
SSL_VERIFY_DEFAULT: bool = False
