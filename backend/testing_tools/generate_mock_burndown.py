"""
Method 3 High-Fidelity Mock Burndown Generator (`backend/testing_tools/generate_mock_burndown.py`)

Generates realistic agile burndown mock data inspired by Method 3: Pure Interpolation & Agile Delta Forecasting.
Simulates:
  - Master Baseline checkpoints (PCHIP Monotonic Interpolation)
  - Live Active Sprint with initial scope creep (+2.1 pts) followed by steady burndown
  - Catch-Up Track (tapering delta to 0)
  - Slip Track (parallel offset)
"""

import json
import numpy as np
from scipy.interpolate import PchipInterpolator
from typing import Dict, Any, List


def generate_method3_mock_burndown() -> Dict[str, Any]:
    """
    Generates high-resolution Method 3 burndown series & forecast tracks.
    """
    N = 10
    x_data = np.linspace(0, 100, N)
    x_max = 100.0

    # 1. Master Baseline Checkpoints (Slow start, rapid drop in week 2)
    y_avg = np.array([100.0, 94.3, 93.1, 91.4, 90.6, 89.3, 85.4, 73.5, 35.5, 2.2])
    master_pchip = PchipInterpolator(x_data, y_avg)

    # 2. Live Active Sprint (Running slightly behind schedule with initial scope creep)
    live_idx = 6
    x_live = x_data[:live_idx]
    y_live = np.array([100.0, 101.5, 102.1, 101.8, 98.4, 90.5])
    current_delta = float(y_live[-1] - y_avg[live_idx - 1])  # Gap at Day 55.6 (+10.4 pts)

    # 3. Smooth Forecast Tracks (200 continuous points)
    x_smooth_future = np.linspace(x_live[-1], x_max, 200)
    slip_smooth = master_pchip(x_smooth_future) + current_delta
    decay_factor = (x_max - x_smooth_future) / (x_max - x_live[-1])
    catchup_smooth = master_pchip(x_smooth_future) + (current_delta * decay_factor)

    # 4. Generate daily series (Sprint Days 0 to 14)
    dates = [
        "2026-07-01", "2026-07-02", "2026-07-03", "2026-07-06", "2026-07-07",
        "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14"
    ]

    series: List[Dict[str, Any]] = []
    for i in range(N):
        x_val = x_data[i]
        base_val = float(y_avg[i])
        ideal_val = float(max(0.0, 100.0 * (1.0 - i / (N - 1))))
        
        if i < live_idx:
            rem_val = float(y_y_val if (y_y_val := y_live[i]) is not None else base_val)
            pred_val = rem_val
        else:
            decay_i = (x_max - x_val) / (x_max - x_data[live_idx - 1])
            rem_val = float(round(y_live[-1], 1))
            pred_val = float(round(base_val + (current_delta * decay_i), 1))

        series.append({
            "date": dates[i],
            "day_index": i,
            "sprint_progress_pct": round(float(x_val), 1),
            "remaining_points": round(rem_val, 1),
            "ideal_points": round(ideal_val, 1),
            "baseline_points": round(base_val, 1),
            "prediction_points": round(max(0.0, pred_val), 1)
        })

    return {
        "sprint_name": "Sprint 1 (Method 3 Model)",
        "start_date": dates[0],
        "end_date": dates[-1],
        "total_planned_points": 100.0,
        "current_delta_points": round(current_delta, 1),
        "series": series,
        "forecast_tracks": {
            "future_x_pct": x_smooth_future.tolist(),
            "catchup_track": catchup_smooth.tolist(),
            "slip_track": slip_smooth.tolist()
        }
    }


import csv
import io

def generate_method3_mock_burndown_csv() -> str:
    """
    Generates high-resolution Method 3 burndown dataset formatted directly as a CSV string.
    """
    data = generate_method3_mock_burndown()
    series = data["series"]
    sprint_name = data["sprint_name"]

    output = io.StringIO(newline="")
    writer = csv.writer(output)

    # Headers
    headers = [
        "record_date", "Sprint", "sprint_progress_pct", "BurndownSP", 
        "BurndownAVGSP", "BurndownPredictionSP", "SPDelta", "CatchUpSP", "SlipSP"
    ]
    writer.writerow(headers)

    current_delta = data["current_delta_points"]

    for pt in series:
        date = pt["date"]
        pct = pt["sprint_progress_pct"]
        rem = pt["remaining_points"]
        base = pt["baseline_points"]
        pred = pt["prediction_points"]
        delta = round(rem - base, 1)
        catchup = pred
        slip = round(base + current_delta, 1)

        writer.writerow([date, sprint_name, pct, rem, base, pred, delta, catchup, slip])

    return output.getvalue()


def main():
    data = generate_method3_mock_burndown()
    csv_content = generate_method3_mock_burndown_csv()
    
    print(csv_content)
    
    csv_output_path = "backend/testing_tools/method3_mock_burndown_output.csv"
    with open(csv_output_path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)
        
    json_output_path = "backend/testing_tools/method3_mock_burndown_output.json"
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"\n[SUCCESS] Method 3 mock burndown dataset saved to:\n  CSV:  {csv_output_path}\n  JSON: {json_output_path}")


if __name__ == "__main__":
    main()
