"""
Burndown Math (`burndown_math.py`)

Implements Method 3: Pure Interpolation & Agile Delta Forecasting.
Uses PCHIP Monotonic Interpolation to build a master baseline from historical
sprints, and applies smooth Delta Decay to forecast Catch-Up and Slip tracks.
"""

import numpy as np
from scipy.interpolate import PchipInterpolator
from typing import Dict, List, Tuple


def compute_forecast_tracks(
    master_x: List[float], 
    master_y: List[float], 
    live_x: List[float], 
    live_y: List[float],
    forecast_resolution: int = 14
) -> Dict[str, List[float]]:
    """
    Computes the Catch-Up and Slip tracks using Method 3.
    
    Args:
        master_x: Progress percentages of historical checkpoints (0 to 100).
        master_y: Averaged remaining points at those checkpoints.
        live_x: Progress percentages of current sprint's checkpoints.
        live_y: Actual remaining points at those checkpoints.
        forecast_resolution: Number of future points to generate.
        
    Returns:
        Dict with 'future_x', 'catchup_y', and 'slip_y' series.
    """
    if len(master_x) < 2 or len(live_x) < 1:
        return {"future_x": [], "catchup_y": [], "slip_y": []}

    # 1. Build the monotonic master interpolator
    master_pchip = PchipInterpolator(master_x, master_y)
    
    # 2. Find the current delta
    current_x = live_x[-1]
    current_y = live_y[-1]
    
    # Clamp current_x to the known master domain
    baseline_at_current = float(master_pchip(min(100.0, max(0.0, current_x))))
    current_delta = current_y - baseline_at_current
    
    # 3. Generate future X points
    x_max = 100.0
    future_x = np.linspace(current_x, x_max, forecast_resolution)
    
    # 4. Calculate tracks
    slip_smooth = master_pchip(future_x) + current_delta
    
    # Linear decay factor from 1.0 down to 0.0
    if x_max == current_x:
        decay_factor = np.zeros_like(future_x)
    else:
        decay_factor = (x_max - future_x) / (x_max - current_x)
        
    catchup_smooth = master_pchip(future_x) + (current_delta * decay_factor)
    
    return {
        "future_x": future_x.tolist(),
        "catchup_y": catchup_smooth.tolist(),
        "slip_y": slip_smooth.tolist()
    }
