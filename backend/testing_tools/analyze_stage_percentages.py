"""
Stage Time Percentage & Relative Normalization Analysis (`backend/testing_tools/analyze_stage_percentages.py`)

Computes both:
1. Current estimate-grouped averages (E2, E4, E8, E16, etc.)
2. Normalized Stage Percentages (Proportion of active engineering effort consumed per stage)
"""

from backend.AnalyticsWorkerFactory.S0_Extractor.github.github_extractor import GitHubExtractor
from backend.AnalyticsWorkerFactory.S1_Normalizer.s1_normalizer import Normalizer
from backend.AnalyticsWorkerFactory.S2_Analyzer.s2_analyzer import Analyzer
from backend.AnalyticsWorkerFactory.S2_Analyzer.math_engines.time_math import TimeMath
import json


def analyze():
    # 1. Fetch mock dataset
    raw_data = GitHubExtractor._generate_mock_data(["2026-07-01", "2026-07-02", "2026-07-03"], "org/repo")
    tickets = Normalizer.normalize_raw_json(raw_data, board_id=1, default_record_date="2026-07-01")

    # 2. Existing Estimate-Grouped Averages
    avg_by_estimate = TimeMath.average_time_by_estimate(tickets)
    avg_in_step = TimeMath.average_time_in_step(tickets)

    # 3. Calculate Normalized Relative Stage Percentages (Proportion of Active Effort per Stage)
    valid_tickets = [t for t in tickets if (t.time_in_progress_sec + t.time_in_review_sec + getattr(t, "time_in_dev_testing_sec", 0.0) + t.time_in_rework_sec) > 0]
    
    total_active_sec = sum(t.time_in_progress_sec + t.time_in_review_sec + getattr(t, "time_in_dev_testing_sec", 0.0) + t.time_in_rework_sec for t in valid_tickets)
    
    if total_active_sec > 0:
        pct_in_progress = (sum(t.time_in_progress_sec for t in valid_tickets) / total_active_sec) * 100.0
        pct_in_review = (sum(t.time_in_review_sec for t in valid_tickets) / total_active_sec) * 100.0
        pct_dev_testing = (sum(getattr(t, "time_in_dev_testing_sec", 0.0) for t in valid_tickets) / total_active_sec) * 100.0
        pct_rework = (sum(t.time_in_rework_sec for t in valid_tickets) / total_active_sec) * 100.0
    else:
        pct_in_progress = pct_in_review = pct_dev_testing = pct_rework = 0.0

    # 4. Normalized Effort Ratio per Story Point (Hours per Point per Stage)
    # Assuming 1.5 = 1 hour or 1 Story Point = 8 hours
    point_ratios = []
    for t in tickets:
        est = t.estimate if t.estimate > 0 else 1.0
        active_hours = (t.time_in_progress_sec + t.time_in_review_sec + getattr(t, "time_in_dev_testing_sec", 0.0) + t.time_in_rework_sec) / 3600.0
        ratio = active_hours / est
        point_ratios.append({
            "ticket_id": t.ticket_id,
            "estimate": est,
            "active_hours": round(active_hours, 2),
            "hours_per_point": round(ratio, 2)
        })

    print("=" * 70)
    print(" 1. CURRENT ESTIMATE-GROUPED AVERAGES (Fragmented by Size)")
    print("=" * 70)
    print(json.dumps(avg_by_estimate, indent=2))

    print("\n" + "=" * 70)
    print(" 2. SPRINT-WIDE STAGE CYCLE AVERAGES (Days)")
    print("=" * 70)
    print(json.dumps(avg_in_step, indent=2))

    print("\n" + "=" * 70)
    print(" 3. PROPOSED RELATIVE STAGE PERCENTAGES (% of Active Engineering Hour)")
    print("=" * 70)
    print(f"  - In Progress:  {pct_in_progress:>6.2f}%")
    print(f"  - In Review:    {pct_in_review:>6.2f}%")
    print(f"  - Dev Testing:  {pct_dev_testing:>6.2f}%")
    print(f"  - Rework:       {pct_rework:>6.2f}%")
    print(f"  Total:          100.00%")

    print("\n" + "=" * 70)
    print(" 4. EFFORT DENSITY RATIO (Hours per Estimate Point)")
    print("=" * 70)
    for pr in point_ratios:
        print(f"  Ticket {pr['ticket_id']:<8} | Est: {pr['estimate']:>4.1f} SP | Active: {pr['active_hours']:>5.2f}h | Density: {pr['hours_per_point']:>5.2f} hrs/SP")

if __name__ == "__main__":
    analyze()
