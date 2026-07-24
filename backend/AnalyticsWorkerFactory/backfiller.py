import copy
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.AnalyticsWorkerFactory.S0_Extractor.github.timeline_parser import parse_issue_timeline, parse_iso_date
from backend.AnalyticsWorkerFactory.S0_Extractor.github.utils import detect_sprint_window

class BackfillEngine:
    """
    Acts as a wrapper engine around the AnalyticsWorkerFactory.
    It takes the raw JSON payload, rewinds the tickets' statuses and timelines
    iteratively for every day in the sprint, and recursively runs the Factory
    to generate an accurate historical snapshot for each day.
    """
    @staticmethod
    def execute(payload: Dict[str, Any]) -> str:
        raw_json = payload.get("raw_json", {})
        work_items = raw_json.get("workItems", [])
        
        # 1. Detect sprint window
        sprint_meta = detect_sprint_window(work_items)
        sprint_start = sprint_meta.get("start_date")
        sprint_end = sprint_meta.get("end_date")
        
        if not sprint_start or not sprint_end:
            # Fallback to 14 days ending on record_date if detection fails
            record_date_dt = datetime.strptime(payload.get("record_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
            sprint_end_dt = record_date_dt
            sprint_start_dt = sprint_end_dt - timedelta(days=13)
        else:
            sprint_start_dt = datetime.strptime(sprint_start, "%Y-%m-%d")
            sprint_end_dt = datetime.strptime(sprint_end, "%Y-%m-%d")
            
        record_date_iso = payload.get("record_date", datetime.now().strftime("%Y-%m-%d"))
        record_date_dt = datetime.strptime(record_date_iso, "%Y-%m-%d")
        
        # Loop bounds: from sprint_start up to record_date (or sprint_end if record_date > sprint_end)
        loop_end = min(record_date_dt, sprint_end_dt)
        
        # We need to import AnalyticsWorkerFactory dynamically to avoid circular imports
        from backend.AnalyticsWorkerFactory.worker_factory import AnalyticsWorkerFactory
        
        left_rows_by_date = {}
        headers = []
        gap_idx = 33
        
        # We want to capture the FINAL day's Right Side (Sprint Timeline) and Headers
        final_csv_content = ""
        
        current_dt = sprint_start_dt
        while current_dt <= loop_end:
            target_date_iso = current_dt.strftime("%Y-%m-%d")
            # 23:59:59 of that day
            target_date_ts = current_dt.replace(hour=23, minute=59, second=59).timestamp()
            
            # Clone and Time-Travel the Payload
            cloned_payload = copy.deepcopy(payload)
            cloned_payload["backfill"] = False # Prevent infinite recursion!
            cloned_payload["record_date"] = target_date_iso
            
            valid_items = []
            for w in cloned_payload.get("raw_json", {}).get("workItems", []):
                created_ts = parse_iso_date(w.get("createdAt", ""))
                if created_ts > target_date_ts:
                    continue # Ticket didn't exist yet on this day!
                    
                raw_timeline = w.get("raw_timeline", [])
                
                # Recalculate based on chopped timeline
                metrics = parse_issue_timeline(raw_timeline, w.get("createdAt", ""), target_date_ts=target_date_ts)
                
                w["time_in_todo_sec"] = metrics.get("time_in_todo_sec", 0.0)
                w["time_in_progress_sec"] = metrics.get("time_in_progress_sec", 0.0)
                w["time_in_review_sec"] = metrics.get("time_in_review_sec", 0.0)
                w["time_in_rework_sec"] = metrics.get("time_in_rework_sec", 0.0)
                w["rework_loops"] = metrics.get("rework_loops", 0)
                
                # Update status
                w["state"] = metrics.get("current_status", "Todo")
                
                valid_items.append(w)
                
            cloned_payload["raw_json"]["workItems"] = valid_items
            
            # Run the pristine Factory for this specific rewound day
            result = AnalyticsWorkerFactory.execute(cloned_payload)
            daily_csv = result.get("graphic_contract", "")
            
            # Parse the daily CSV to extract just its Left Side for the target_date
            reader = csv.reader(io.StringIO(daily_csv))
            daily_headers = next(reader, [])
            if not headers:
                headers = daily_headers
                # Dynamically find gap_idx
                for i in range(len(headers) - 1):
                    if headers[i] == "" and headers[i+1] == "" and len(headers) > i+2 and headers[i+2] != "":
                        gap_idx = i
                        break
                        
            # In the generated 14-day CSV, there is exactly ONE row that matches target_date_iso
            for row in reader:
                if not row: continue
                if row[0] == target_date_iso:
                    left_rows_by_date[target_date_iso] = row[:gap_idx]
                    
            if current_dt == loop_end:
                # Capture the final right side timeline (which is accurate as of TODAY)
                final_csv_content = daily_csv
                
            current_dt += timedelta(days=1)
            
        # Stitch it all together!
        # Read the final_csv_content, overwrite the left side if we have a backfilled row
        final_reader = csv.reader(io.StringIO(final_csv_content))
        _ = next(final_reader, []) # skip headers
        
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for row in final_reader:
            if not row: continue
            r_date = row[0]
            
            left = row[:gap_idx]
            separator = row[gap_idx:gap_idx+2] if len(row) >= gap_idx+2 else ["", ""]
            right = row[gap_idx+2:] if len(row) > gap_idx+2 else []
            
            if r_date in left_rows_by_date:
                left = left_rows_by_date[r_date]
            else:
                # If it's in the future (after loop_end), blank out the actuals
                if r_date > record_date_iso:
                    # Blank out indices 2 through 29 (issues_total up to BurndownSP)
                    for i in range(2, min(30, len(left))):
                        left[i] = ""
                    # Also blank out SPDelta (index 32)
                    if len(left) > 32:
                        left[32] = ""
                        
            writer.writerow(left + separator + right)
            
        return output.getvalue()
