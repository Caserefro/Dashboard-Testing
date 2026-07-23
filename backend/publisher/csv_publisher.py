"""
CSV Publisher Worker (`backend/publisher/csv_publisher.py`)

A background worker meant to be invoked as a detached subprocess by the Orchestrator.
Receives the Formatter's output via sys.stdin (which will contain the CSV string if 
output_format="csv" was used) and dumps it cleanly to the local disk.
"""

import sys
import json
import os

def main():
    # 1. Read the factory payload from stdin
    input_data = sys.stdin.read()
    if not input_data:
        print("[CSV Publisher] No data received on stdin.", file=sys.stderr)
        sys.exit(1)
        
    try:
        payload = json.loads(input_data)
        board_id = payload.get("board_id", "UNKNOWN")
        csv_contract = payload.get("graphic_contract", "")
        
        print(f"[CSV Publisher] Writing CSV dump for board {board_id}...")
        
        # 2. Dump the CSV string directly to the local disk
        output_path = os.path.join(os.path.dirname(__file__), "..", "..", f"dashboard_data_{board_id}.csv")
        output_path = os.path.abspath(output_path)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(csv_contract)
            
        print(f"[CSV Publisher] Successfully dumped metrics to {output_path}!")
        sys.exit(0)
        
    except Exception as e:
        print(f"[CSV Publisher] Failed to parse input or write CSV: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
