import csv
from itertools import zip_longest

def generate_mock_csv():
    output_path = "mock_dashboard_data.csv"
    
    # 14-day sprint
    dates = [f"2026-07-{i:02d}" for i in range(1, 16)]
    sprint_name = "Sprint 14"
    
    # --- LEFT SIDE HEADERS ---
    left_headers = [
        "record_date", "Sprint", "issues_total", "issues_todo", "issues_in_progress", "issues_in_review", "issues_merged",
        "avg_time_todo_E2", "avg_time_in_progress_E2", "avg_time_in_review_E2", "avg_time_merged_E2",
        "avg_time_todo_E4", "avg_time_in_progress_E4", "avg_time_in_review_E4", "avg_time_merged_E4",
        "avg_time_todo_E8", "avg_time_in_progress_E8", "avg_time_in_review_E8", "avg_time_merged_E8",
        "avg_time_todo_E16", "avg_time_in_progress_E16", "avg_time_in_review_E16", "avg_time_merged_E16",
        "story_points_total", "story_points_bug", "story_points_non_bug", "story_points_clean_pct",
        "average_prs_per_issue", "reentries_per_issue",
        "BurndownSP", "BurndownAVGSP", "BurndownPredictionSP", "SPDelta"
    ]
    
    # Realistic Burndown Math (Day 1 to 15)
    # The sprint "currently" is on Day 11 (2026-07-11)
    burndown_actuals = [100.0, 100.0, 95.0, 85.0, 85.0, 70.0, 65.0, 60.0, 50.0, 40.0, 32.0, "", "", "", ""]
    
    # A PCHIP-like historical curve
    burndown_avg = [100.0, 98.0, 95.0, 90.0, 85.0, 78.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0, 5.0, 0.0]
    
    # Prediction tapers the gap from 32 (current) to a slip finish of +3.0 pts
    pred_vals = [0]*15
    for i in range(11, 15):
        # linear interpolation from 32 to 3.0 over the last 4 days
        pred_vals[i] = 32.0 - ((32.0 - 3.0) / 4) * (i - 10)
    
    left_rows = []
    for i, date in enumerate(dates):
        actual = burndown_actuals[i]
        prediction = actual if actual != "" else round(pred_vals[i], 2)
        
        # Calculate Delta
        baseline = burndown_avg[i]
        if actual != "":
            sp_delta = round(actual - baseline, 2)
        else:
            sp_delta = round(prediction - baseline, 2)
            
        # Realistic issue flows
        todo = max(0, 25 - (i * 2))
        merged = min(25, int(i * 1.5))
        inp = 25 - todo - merged - 2
        inrev = 2
        
        left_rows.append([
            date, sprint_name, 25, todo, max(0, inp), max(0, inrev), merged,
            # Cycle Times
            0.5, 1.2, 0.8, 2.5,   # E2
            1.0, 2.5, 1.0, 4.5,   # E4
            2.0, 5.0, 2.0, 9.0,   # E8
            3.0, 8.0, 4.0, 15.0,  # E16
            # SP & Quality Metrics
            100.0, 15.0, 85.0, 85.0,
            1.2, 0.4,
            # Burndown
            actual, round(baseline, 2), prediction, sp_delta
        ])

    # --- RIGHT SIDE HEADERS ---
    right_headers = ["Title", "Sprint", "TodoDays", "InProgressDays", "InReviewDays", "ReworkDays"]
    right_rows = []
    
    for i in range(1, 26):
        title = f"Database Migration Phase {i}" if i < 15 else f"Fix UI Alignment Bug #{i}"
        
        status = "TODO"
        if i <= 15:
            status = "DONE"
        elif i <= 20:
            status = "IN_PROGRESS"
        elif i <= 25:
            status = "IN_REVIEW"
            
        todo_d = round(0.5 + i*0.2, 1)
        inp_d = round(1.0 + (i%4)*0.8, 1) if status != "TODO" else 0.0
        inr_d = round(0.5 + (i%2)*0.5, 1) if status in ["IN_REVIEW", "DONE"] else 0.0
        
        # Inject realistic rework into 3 specific tickets
        rew_d = 2.5 if i in [5, 12, 19] else 0.0
        
        right_rows.append([title, sprint_name, todo_d, inp_d, inr_d, rew_d])
        
    # Write stitched CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(left_headers + ["", ""] + right_headers)
        
        for left, right in zip_longest(left_rows, right_rows, fillvalue=[]):
            l_pad = left if left else [""]*len(left_headers)
            r_pad = right if right else [""]*len(right_headers)
            writer.writerow(l_pad + ["", ""] + r_pad)
            
    print(f"Mock data generated successfully at {output_path}!")

if __name__ == "__main__":
    generate_mock_csv()
