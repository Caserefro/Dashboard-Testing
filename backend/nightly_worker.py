"""
Nightly Worker (`backend/nightly_worker.py`)

Background polling daemon. Runs decoupled from FastAPI.
Uses the same singletons (Repository, SyncService) via dependencies.py.
"""

import time
import json
from datetime import datetime, timezone
from backend.dependencies import sync_service


def run_continuous_sync(board_id: int = 10, interval_seconds: int = 10):
    print("=" * 70)
    print(f"  PROJECT ATLAS - NIGHTLY WORKER (Polling every {interval_seconds}s)")
    print("=" * 70)

    while True:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"\n[{now}] Syncing Board {board_id}...")

        result = sync_service.run_sync(board_id=board_id)

        if result.success:
            contract_size = len(json.dumps(result.graphic_contract))
            fty = result.graphic_contract.get("first_time_yield_gauge", {}).get("fty_percentage", 0)
            print(f"  [OK] Contract: {contract_size} bytes | FTY: {fty}%")
        else:
            print(f"  [FAIL] {result.error}")

        print(f"[{now}] Sleeping...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_continuous_sync(board_id=10, interval_seconds=10)
