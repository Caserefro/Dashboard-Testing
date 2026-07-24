"""
Burndown Math (`burndown_math.py`)

Implements Method 3: Pure Interpolation & Agile Delta Forecasting.
Uses PCHIP Monotonic Interpolation to build a master baseline from historical
sprints, and applies smooth Delta Decay to forecast Catch-Up and Slip tracks.
"""

import numpy as np
import math
from scipy.interpolate import PchipInterpolator
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from backend.domain.process_data_models import NormalizedTicket

class BurndownMath:
    @staticmethod
    def burndown_curve(
        tickets: List[NormalizedTicket],
        start_date_iso: str,
        end_date_iso: str,
        total_ideal_points: Optional[float] = None,
        historical_od: Optional[List[Dict[str, Any]]] = None,
        record_date_iso: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes the daily burndown curve series (`remaining_points`, `ideal_points`, `inverse_root_points`).
        Integrates Method 3: PCHIP Forecasting.
        """
        try:
            start_dt = datetime.strptime(start_date_iso[:10], "%Y-%m-%d")
            end_dt = datetime.strptime(end_date_iso[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            start_dt = datetime.now() - timedelta(days=14)
            end_dt = datetime.now()
            
        try:
            record_dt = datetime.strptime(record_date_iso[:10], "%Y-%m-%d") if record_date_iso else datetime.now()
        except (ValueError, TypeError):
            record_dt = datetime.now()

        total_days = max(1, (end_dt - start_dt).days)

        if total_ideal_points is None or total_ideal_points <= 0:
            total_ideal_points = sum(t.story_points for t in tickets) if tickets else 100.0

        # 1. Build Master Baseline from historical_od (fallback to ideal if none)
        master_x = [0.0, 100.0]
        master_y = [total_ideal_points, 0.0]
        if historical_od and len(historical_od) >= 2:
            master_x.clear()
            master_y.clear()
            hist_len = len(historical_od)
            for i, record in enumerate(historical_od):
                master_x.append((i / (hist_len - 1)) * 100.0)
                master_y.append(float(record.get("remaining_story_points", 0.0)))
                
        # Handle duplicate x-values (PCHIP requirement)
        if len(set(master_x)) < len(master_x):
            master_x = [0.0, 100.0]
            master_y = [total_ideal_points, 0.0]

        master_pchip = PchipInterpolator(master_x, master_y)

        # 2. Extract live points up to today
        live_x = []
        live_y = []
        for day_offset in range(total_days + 1):
            current_dt = start_dt + timedelta(days=day_offset)
            current_date_str = current_dt.strftime("%Y-%m-%d")
            
            # Stop collecting live points if we are past TODAY (the record date)
            if current_dt > record_dt:
                break
                
            daily_completed = sum(
                t.story_points for t in tickets
                if t.status_normalized == "DONE" and t.completed_date and t.completed_date <= current_date_str
            )
            
            x_percent = (day_offset / total_days) * 100.0
            remaining = max(0.0, total_ideal_points - daily_completed)
            live_x.append(x_percent)
            live_y.append(remaining)

        current_x = live_x[-1] if live_x else 0.0
        current_y = live_y[-1] if live_y else total_ideal_points
        baseline_at_current = float(master_pchip(min(100.0, max(0.0, current_x))))
        current_delta = current_y - baseline_at_current

        # 3. Generate the full daily series array
        series: List[Dict[str, Any]] = []
        for day_offset in range(total_days + 1):
            current_dt = start_dt + timedelta(days=day_offset)
            current_date_str = current_dt.strftime("%Y-%m-%d")
            x_percent = (day_offset / total_days) * 100.0
            
            # Straight-line Ideal
            ideal = max(0.0, total_ideal_points * (1.0 - day_offset / total_days))
            inv_root = max(0.0, total_ideal_points * (1.0 - math.sqrt(day_offset / total_days)))
            
            # Historical Baseline (The Real "AVG")
            hist_baseline = float(master_pchip(x_percent))
            
            # Actual Remaining
            daily_completed = sum(
                t.story_points for t in tickets
                if t.status_normalized == "DONE" and t.completed_date and t.completed_date <= current_date_str
            )
            actual_remaining = max(0.0, total_ideal_points - daily_completed)
            
            # Catchup Prediction
            if x_percent <= current_x:
                prediction = actual_remaining  # In the past/present, prediction is reality
            else:
                decay_factor = (100.0 - x_percent) / (100.0 - current_x) if current_x < 100.0 else 0.0
                prediction = hist_baseline + (current_delta * decay_factor)
                
            series.append({
                "date": current_date_str,
                "remaining_points": round(actual_remaining, 2) if current_dt <= record_dt else round(current_y, 2),
                "ideal_points": round(ideal, 2),
                "baseline_points": round(hist_baseline, 2),
                "prediction_points": round(max(0.0, prediction), 2),
                "inverse_root_points": round(inv_root, 2),
            })
            
        forecast = BurndownMath.compute_forecast_tracks(master_x, master_y, live_x, live_y)

        return {
            "series": series,
            "forecast": forecast
        }

    @staticmethod
    def compute_forecast_tracks(
        master_x: List[float], 
        master_y: List[float], 
        live_x: List[float], 
        live_y: List[float],
        forecast_resolution: int = 14
    ) -> Dict[str, List[float]]:
        """
        Computes the Catch-Up and Slip tracks using Method 3.
        """
        if len(master_x) < 2 or len(live_x) < 1:
            return {"future_x": [], "catchup_y": [], "slip_y": [], "forecast_y": []}

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
            "slip_y": slip_smooth.tolist(),
            "forecast_y": catchup_smooth.tolist() # Fallback mapping to 'forecast_y' for S3 Formatter
        }
