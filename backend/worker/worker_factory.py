"""
Unified Analytics Worker Factory (`worker_factory.py`)

Pure Factory Pattern execution:
Orchestrates the sequential, in-memory pipeline (`Normalizer -> Analyzer -> Formatter`) within a single process.
Avoids zero unnecessary serialization/pickling copies to achieve sub-millisecond execution inside the container:
`docker run --network=none --memory=512m --rm -i analytics-worker:latest`

Input:  Single JSON bundle via sys.stdin  (`Raw Json + OD + KPI Config`)
Output: 2-part JSON via sys.stdout        (`kpi_record_for_db` + `graphic_contract`)
"""

import sys
import json
from typing import Dict, Any, List, Tuple
from backend.worker.s1_normalizer import Normalizer
from backend.worker.s2_analyzer import Analyzer
from backend.worker.s3_formatter import Formatter
from backend.models.process_data_models import ProcessDataAggregate


class AnalyticsWorkerFactory:
    """Pure Factory orchestrator coordinating Normalizer, Analyzer, and Formatter entities."""

    @classmethod
    def execute(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the 3-stage pure factory pipeline:
          1. Normalizer (`Creates Process Data`)
          2. Analyzer (`Gives meaning to data`)
          3. Formatter (`Gives shape to data`)
        """
        board_id = int(payload.get("board_id", 1))
        record_date = str(payload.get("record_date", "2026-07-12"))[:10]
        raw_json = payload.get("raw_json", {})
        orchestrator_data_od = payload.get("orchestrator_data_od", [])
        kpi_config = payload.get("kpi_config", {})
        output_format = payload.get("output_format", "graphic_contract").lower()
        start_date = payload.get("start_date", record_date)
        end_date = payload.get("end_date", record_date)

        # ============================================================== #
        # ============================================================== #
        #  STAGE 1: NORMALIZER (`Creates Process Data`)
        # ============================================================== #
        new_tickets, old_tickets, new_prs = Normalizer.normalize_all(
            raw_json=raw_json,
            orchestrator_data_od=orchestrator_data_od,
            board_id=board_id,
            record_date=record_date
        )

        # Combine cleanly in RAM: `O(1)` pointer list concatenation (Zero serialization copies)
        combined_tickets = old_tickets + new_tickets

        # ============================================================== #
        #  STAGE 2: ANALYZER (`Gives Meaning to Data`)
        # ============================================================== #
        computed_kpis = Analyzer.measure_all(
            tickets=combined_tickets,
            start_date=start_date,
            end_date=end_date,
            kpi_config=kpi_config
        )

        # ============================================================== #
        #  STAGE 3: FORMATTER (`Gives Shape to Data`)
        # ============================================================== #
        return Formatter.format_all(
            board_id=board_id,
            record_date=record_date,
            computed_kpis=computed_kpis,
            tickets=combined_tickets,
            prs=new_prs,
            total_ideal_points=kpi_config.get("total_ideal_points"),
            output_format=output_format
        )


# ================================================================== #
#  Container entrypoint (sys.stdin -> AnalyticsWorkerFactory -> sys.stdout)
# ================================================================== #

def main() -> None:
    """Main entrypoint when invoked inside Docker or from command line."""
    import tracemalloc
    import os

    tracemalloc.start()
    try:
        input_data = sys.stdin.read()
        payload = json.loads(input_data) if input_data.strip() else {}

        output = AnalyticsWorkerFactory.execute(payload)

        sys.stdout.write(json.dumps(output, indent=2))
        sys.stdout.flush()

        # Measure memory footprint and log clean diagnostic to sys.stderr
        current_py, peak_py = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        py_peak_mb = round(peak_py / (1024 * 1024), 3)

        # Try reading Linux cgroup peak memory if running inside Docker container
        cgroup_peak_mb = "N/A"
        try:
            if os.path.exists("/sys/fs/cgroup/memory.peak"):
                with open("/sys/fs/cgroup/memory.peak", "r") as f:
                    cgroup_peak_mb = f"{round(int(f.read().strip()) / (1024 * 1024), 2)} MB"
            elif os.path.exists("/sys/fs/cgroup/memory/memory.max_usage_in_bytes"):
                with open("/sys/fs/cgroup/memory/memory.max_usage_in_bytes", "r") as f:
                    cgroup_peak_mb = f"{round(int(f.read().strip()) / (1024 * 1024), 2)} MB"
        except Exception:
            pass

        sys.stderr.write(
            f"\n[ATLAS WORKER MEMORY AUDIT] Python Heap Peak: {py_peak_mb} MB | Container OS Peak: {cgroup_peak_mb} | Sandbox Limit: 512.0 MB\n"
        )
        sys.stderr.flush()
        sys.exit(0)
    except Exception as e:
        error = {"error": "AnalyticsWorkerFactoryExecutionError", "details": str(e)}
        sys.stderr.write(json.dumps(error) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
