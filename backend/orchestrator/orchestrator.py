"""
Orchestrator Facade (`backend/orchestrator/orchestrator.py`)

Domain Layer facade.
This module encapsulates the complexity of the data pipeline.

Responsibilities:
  1. SQL Gap Detection: Checks what dates are missing from the DB.
  2. Triggers S0 Extractors via subprocess pipes for the missing dates.
  3. Triggers the Factory Worker (S1->S2->S3) to normalize, analyze, and format.
  4. Generates the SQL UPSERT command to write the metrics back to Postgres.
  
The Orchestrator is instantiated per sync cycle and dies immediately after, holding zero state.
"""

import sys
import subprocess
import json
import base64
from typing import List, Set, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from backend.worker.worker_factory import AnalyticsWorkerFactory

from backend.repository.crypto import KeyVaultMemoryCodec


class DockerWorkerOrchestrator:
    """
    Orchestrator facade. Created per sync call, dies when the call ends.
    Coordinates data extraction and metric calculation via subprocess creation.
    """

    def __init__(self, master_key_base64: Optional[str] = None):
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

        module_name = "backend.worker.S0_Extractor.azure_extractor"
        if "github" in extractor_image_or_script.lower():
            module_name = "backend.worker.S0_Extractor.github_extractor"

        cmd = [sys.executable, "-m", module_name]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout_val, stderr_val = process.communicate(input=json.dumps(extractor_payload))

        if process.returncode != 0:
            raise RuntimeError(f"Extractor process ({module_name}) failed: {stderr_val}")

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

        return AnalyticsWorkerFactory.execute(worker_payload)

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
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, Any]]]:
        """
        Master orchestration cycle (`Syncs Data Extraction and Docker Worker`).
        Returns `(Graphic contract dict for Data Sync/GUI, SQL UPSERT string for DB, KPI records snapshot)`.
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

        return graphic_contract, sql_upsert, kpi_record_for_db

    def compute_contract_from_db_records(
        self,
        board_id: int,
        kpi_config: Dict[str, Any],
        start_date: str,
        end_date: str,
        existing_db_process_data_od: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Offline Query Engine (`Read Side / CQRS Projection`).
        Takes canonical Process Data / Historical OD stored in Postgres (`kpi_records_daily`)
        and projects them through `Normalizer -> Analyzer -> Formatter` (`trigger_analizer_worker`)
        in pure RAM (< 2ms) without triggering external network API extractions (`trigger_extractor_layer`).
        """
        worker_output = self.trigger_analizer_worker(
            board_id=board_id,
            record_date=end_date,
            raw_json_dump={},  # Offline mode: zero network extraction
            orchestrator_data_od=existing_db_process_data_od,
            kpi_config=kpi_config,
            start_date=start_date,
            end_date=end_date
        )
        return worker_output.get("graphic_contract", {})



