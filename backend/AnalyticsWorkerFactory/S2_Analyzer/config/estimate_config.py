"""
Stage 2: Analyzer Estimation Configuration (`backend/worker/S2_Analyzer/config/estimate_config.py`)

Single Responsibility: Configures analytical estimate grouping (RAW vs BUCKETED) and size ranges.
"""

from typing import Dict, Any

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
