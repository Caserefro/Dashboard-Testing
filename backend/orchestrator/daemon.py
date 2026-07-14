"""
Docker Worker Orchestrator (`daemon.py`)

As defined in the Miro architecture:
1. Syncs Data Extraction (`extractor-api`) and Analizer Worker (`analytics-worker`), avoiding still instances.
2. Receives requested Data Period, checks Postgres for existing records (`SQL Gap Detection`).
3. Sends only missing dates + decrypted API keys (via memory `stdin` pipes) to `Dockerized API extractors`.
4. Packages `Orchestrator Data (OD)`: `DB Process Data` + `KPI Config` + `Raw JSON` -> sends to `Analizer Worker`.
5. Executes SQL `UPSERT` (`INSERT ... ON CONFLICT DO UPDATE`) to save `KPI_Record for DB` (`process_data_json`).
"""

import sys
import subprocess
import json
import base64
from typing import List, Set, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from backend.worker.worker_factory import AnalyticsWorkerFactory

# Lightweight optional encryption support if cryptography is installed
try:
    from cryptography.fernet import Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


class KeyVaultMemoryCodec:
    """No-Server-Hassle memory encryption using Fernet AES-256 for Data API keys at rest."""
    def __init__(self, master_key_base64: Optional[str] = None):
        if not _CRYPTO_AVAILABLE:
            self.cipher = None
            return
        if not master_key_base64:
            # Generate a consistent session key if none provided
            self.cipher = Fernet(Fernet.generate_key())
        else:
            self.cipher = Fernet(master_key_base64.encode("utf-8"))

    def encrypt_key(self, raw_api_key: str) -> str:
        if not self.cipher or not raw_api_key:
            return raw_api_key
        return self.cipher.encrypt(raw_api_key.encode("utf-8")).decode("utf-8")

    def decrypt_key(self, encrypted_api_key: str) -> str:
        if not self.cipher or not encrypted_api_key:
            return encrypted_api_key
        try:
            return self.cipher.decrypt(encrypted_api_key.encode("utf-8")).decode("utf-8")
        except Exception:
            return encrypted_api_key


class DockerWorkerOrchestrator:
    """The persistent Conductor managing data extraction and offline metric calculation."""
    
    def __init__(self, use_docker_containers: bool = False, master_key_base64: Optional[str] = None):
        """
        :param use_docker_containers: If True, invokes `docker run` via subprocess.
                                      If False (local development/testing), invokes Python pipelines directly in memory.
        """
        self.use_docker_containers = use_docker_containers
        self.key_codec = KeyVaultMemoryCodec(master_key_base64)

    def identify_missing_date_gap(
        self,
        requested_start_date: str,
        requested_end_date: str,
        existing_db_dates: Set[str]
    ) -> List[str]:
        """
        Step 1: SQL Gap Detection (`identifies what is on DB and what needs Requesting based on date field`).
        Subtracts existing database dates from requested window using set math.
        """
        try:
            start_dt = datetime.strptime(requested_start_date[:10], "%Y-%m-%d")
            end_dt = datetime.strptime(requested_end_date[:10], "%Y-%m-%d")
        except ValueError:
            return [requested_start_date[:10]]

        total_days = max(1, (end_dt - start_dt).days + 1)
        requested_set = { (start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(total_days) }
        
        missing_dates = sorted(list(requested_set - existing_db_dates))
        return missing_dates

    def trigger_extractor_layer(
        self,
        board_id: int,
        missing_dates: List[str],
        encrypted_api_key: str,
        extractor_image_or_script: str = "extractor-api:latest"
    ) -> Dict[str, Any]:
        """
        Step 2: Spawns `Dockerized API extractors` via `stdin` memory pipe.
        Passes `Required Time Period` + decrypted `Data API keys`. Returns `Dump 100% Raw JSON`.
        """
        if not missing_dates:
            return {"workItems": []}  # Zero extraction needed when DB already has all dates!

        decrypted_key = self.key_codec.decrypt_key(encrypted_api_key)
        extractor_payload = {
            "board_id": board_id,
            "api_key": decrypted_key,
            "missing_dates": missing_dates
        }

        if not self.use_docker_containers:
            # Single Container / Subprocess Mode (`python -m backend.extractors.azure_extractor`)
            module_name = "backend.extractors.azure_extractor"
            if "github" in extractor_image_or_script.lower():
                module_name = "backend.extractors.github_extractor"
            cmd = [sys.executable, "-m", module_name]
        else:
            # Multi-Container DooD Mode (`docker run -i --rm azure-extractor:latest`)
            cmd = ["docker", "run", "-i", "--rm", extractor_image_or_script]

        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout_val, stderr_val = process.communicate(input=json.dumps(extractor_payload))
        
        if process.returncode != 0:
            raise RuntimeError(f"Extractor process ({cmd[0]}) failed: {stderr_val}")
        
        return json.loads(stdout_val)

    def trigger_analizer_worker(
        self,
        board_id: int,
        record_date: str,
        raw_json_dump: Dict[str, Any],
        orchestrator_data_od: List[Dict[str, Any]],
        kpi_config: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Step 3: Packages `Orchestrator Data (OD)` (`DB Process Data` + `KPI Config` + `Raw JSON`)
        and triggers `Analizer Worker` (`docker run --network=none analytics-worker`).
        """
        worker_payload = {
            "board_id": board_id,
            "record_date": record_date,
            "start_date": start_date,
            "end_date": end_date,
            "raw_json": raw_json_dump,
            "orchestrator_data_od": orchestrator_data_od,
            "kpi_config": kpi_config,
            "output_format": "graphic_contract"
        }

        if not self.use_docker_containers:
            # Execute Python worker pipeline directly in RAM using our 2-Thread engine
            return AnalyticsWorkerFactory.execute(worker_payload)

        # Sandboxed Docker Worker execution (`docker run -i --network=none --memory=512m --rm ...`)
        cmd = ["docker", "run", "-i", "--network=none", "--memory=512m", "--rm", "analytics-worker:latest"]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout_val, stderr_val = process.communicate(input=json.dumps(worker_payload))

        if process.returncode != 0:
            raise RuntimeError(f"Analizer worker container failed: {stderr_val}")

        return json.loads(stdout_val)

    def generate_sql_upsert_command(self, board_id: int, kpi_config_id: int, record_date: str, process_data_json: str) -> str:
        """
        Step 4: Daily Record Overwrite Rule (`INSERT ... ON CONFLICT DO UPDATE`).
        Generates the exact Postgres SQL UPSERT query to save `KPI_Record for DB`.
        """
        # Stage 3: Generate SQL UPSERT statement using exact KPI_RECORDS_DAILY schema (`metrics_json`)
        # Schema: record_id (PK), kpi_config_id (FK), record_date (date), metrics_json (string), comments (string), created_by (int)
        created_by = 1
        comments = "Automated Hephaestus Worker Sync"
        db_record_escaped = process_data_json.replace("'", "''")

        sql_upsert = (
            f"INSERT INTO kpi_records_daily (kpi_config_id, record_date, metrics_json, comments, created_by) "
            f"VALUES ({kpi_config_id}, '{record_date}', '{db_record_escaped}', '{comments}', {created_by}) "
            f"ON CONFLICT (kpi_config_id, record_date) "
            f"DO UPDATE SET metrics_json = EXCLUDED.metrics_json, comments = EXCLUDED.comments;"
        )
        return sql_upsert

    def run_sync_cycle(
        self,
        board_id: int,
        kpi_config_id: int,
        requested_start_date: str,
        requested_end_date: str,
        existing_db_dates: Set[str],
        existing_db_process_data_od: List[Dict[str, Any]],
        encrypted_api_key: str,
        kpi_config: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """
        Master orchestration cycle (`Syncs Data Extraction and Docker Worker`).
        Returns `(Graphic contract dict for Data Sync/GUI, SQL UPSERT string for DB)`.
        """
        # 1. Check gap
        missing_dates = self.identify_missing_date_gap(requested_start_date, requested_end_date, existing_db_dates)
        
        # 2. Extract
        raw_dump = self.trigger_extractor_layer(board_id, missing_dates, encrypted_api_key)

        # 3. Analyze (`Normalizer -> Analizer -> Parser`)
        worker_output = self.trigger_analizer_worker(
            board_id=board_id,
            record_date=requested_end_date,
            raw_json_dump=raw_dump,
            orchestrator_data_od=existing_db_process_data_od,
            kpi_config=kpi_config,
            start_date=requested_start_date,
            end_date=requested_end_date
        )

        # 4. Extract outputs
        kpi_record_for_db = worker_output.get("kpi_record_for_db", [])
        graphic_contract = worker_output.get("graphic_contract", {})

        # 5. Generate SQL UPSERT
        process_json_str = json.dumps(kpi_record_for_db)
        sql_upsert = self.generate_sql_upsert_command(board_id, kpi_config_id, requested_end_date, process_json_str)

        return graphic_contract, sql_upsert


def main() -> None:
    """CLI Entrypoint when orchestrator daemon is invoked inside Docker or command line."""
    import sys
    import argparse
    from backend.worker.s1_normalizer import Normalizer

    parser = argparse.ArgumentParser(
        description="Project ATLAS - DockerWorkerOrchestrator Daemon (DooD Container Service)"
    )
    parser.add_argument(
        "--test-sync",
        action="store_true",
        help="Run an end-to-end test sync cycle triggering analytics-worker:latest via Docker-out-of-Docker socket"
    )
    parser.add_argument(
        "--board-id",
        type=int,
        default=10,
        help="Target Board ID to sync (default: 10)"
    )
    parser.add_argument(
        "--kpi-config-id",
        type=int,
        default=42,
        help="Target KPI Config ID (default: 42)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2026-07-01",
        help="Requested start date ISO (default: 2026-07-01)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2026-07-12",
        help="Requested end date ISO (default: 2026-07-12)"
    )

    args = parser.parse_args()

    # If invoked with --help or zero arguments and no --test-sync, print help or run test sync
    if not args.test_sync and len(sys.argv) == 1:
        parser.print_help()
        print("\n💡 Tip: Run `docker run --rm -v //var/run/docker.sock:/var/run/docker.sock orchestrator:latest --test-sync` to test DooD container spawning!")
        sys.exit(0)

    if args.test_sync:
        print("=" * 64)
        print("  PROJECT ATLAS - ORCHESTRATOR DooD CONTAINER SYNC TEST")
        print("=" * 64)
        print(f"[Orchestrator] Starting sync cycle for Board ID: {args.board_id} | Dates: {args.start_date} -> {args.end_date}")

        # Sample dummy data for test-sync run
        sample_raw_json = {
            "workItems": [
                {
                    "id": "AZ-101",
                    "fields": {
                        "System.WorkItemType": "User Story",
                        "System.State": "Done",
                        "Microsoft.VSTS.Scheduling.StoryPoints": "15.0",
                        "System.CreatedDate": "2026-07-01T10:00:00Z",
                        "Microsoft.VSTS.Common.ClosedDate": "2026-07-03T16:00:00Z",
                        "System.Title": "Orchestrator DooD Verification Story"
                    }
                }
            ]
        }
        sample_od = [
            {
                "ticket_id": "AZ-099",
                "unit_type": "USER_STORY",
                "status_normalized": "DONE",
                "story_points": 20.0,
                "created_date": "2026-06-28",
                "completed_date": "2026-07-01",
                "is_first_time_yield": True,
                "board_id": args.board_id
            }
        ]
        sample_kpi_config = {"total_ideal_points": 100.0}

        orchestrator = DockerWorkerOrchestrator(use_docker_containers=True)
        try:
            print("[Orchestrator] Spawning sibling container `analytics-worker:latest` via /var/run/docker.sock...")
            worker_output = orchestrator.trigger_analizer_worker(
                board_id=args.board_id,
                record_date=args.end_date,
                raw_json_dump=sample_raw_json,
                orchestrator_data_od=sample_od,
                kpi_config=sample_kpi_config,
                start_date=args.start_date,
                end_date=args.end_date
            )
            print("  [PASS] Sibling worker container `analytics-worker:latest` executed successfully!")
            
            # Generate SQL UPSERT
            kpi_record_for_db = worker_output.get("kpi_record_for_db", {})
            graphic_contract = worker_output.get("graphic_contract", {})
            sql_upsert = orchestrator.generate_sql_upsert_command(
                board_id=args.board_id,
                kpi_config_id=args.kpi_config_id,
                record_date=args.end_date,
                process_data_json=json.dumps(kpi_record_for_db)
            )

            print("\n--- Generated SQL UPSERT Command (`KPI_RECORDS_DAILY` `metrics_json`) ---")
            print(sql_upsert)
            print("\n--- Returned Graphic Contract Summary (`ui_graph_contracts`) ---")
            print(f"  First Time Yield (FTY): {graphic_contract.get('first_time_yield_gauge', {}).get('fty_percentage')}%")
            print(f"  Burndown Curve Data Points: {len(graphic_contract.get('burndown_curve', []))} days")
            print(f"  Velocity Chart Data Points: {len(graphic_contract.get('tickets_per_day_chart', []))} days")
            print("=" * 64)
            print("  ORCHESTRATOR DooD SYNC CYCLE COMPLETE (100% SUCCESS)")
            print("=" * 64)
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] DooD container sync failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
