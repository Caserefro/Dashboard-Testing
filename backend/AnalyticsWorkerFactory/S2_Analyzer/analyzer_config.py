"""
Stage 2 Analyzer Configuration (`backend/worker/S2_Analyzer/analyzer_config.py`)

Encapsulates all Stage 2 Analyzer settings: estimate bucket modes, forecast resolutions, and outlier threshold rules.
"""

from typing import Dict, Any

# Configurable Estimate Bucket Definition
# MODE options:
#   - "RAW": Outputs exact raw numeric estimate keys (E1, E2, E3, E4, E5, E6, etc.)
#   - "BUCKETED": Maps numeric estimates into the defined ranges below
ESTIMATE_BUCKET_CONFIG: Dict[str, Any] = {
    "MODE": "BUCKETED",  # Maps numeric estimates into E2, E4, E8, E16 standard contract columns
    "RANGES": {
        "E2": (0.0, 3.0),
        "E4": (3.0, 6.0),
        "E8": (6.0, 12.0),
        "E16": (12.0, 999.0)
    }
}

METHOD3_FORECAST_RESOLUTION: int = 14
OUTLIER_IQR_MULTIPLIER: float = 1.5
