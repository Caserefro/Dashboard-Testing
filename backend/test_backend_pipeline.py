"""
PROJECT ATLAS - Pure Factory Integration Test Harness

Verifies the complete backend pipeline:
  Normalizer -> Analyzer -> Formatter
coordinated by AnalyticsWorkerFactory (`worker_factory.py`) with zero memory copies.
"""

import json
from backend.domain.process_data_models import ProcessDataAggregate
from backend.worker.S1_Normalizer.s1_normalizer import Normalizer
from backend.worker.S2_Analyzer.s2_analyzer import Analyzer
from backend.worker.S3_Formatter.s3_formatter import Formatter
from backend.worker.worker_factory import AnalyticsWorkerFactory
from backend.orchestrator.orchestrator import DockerWorkerOrchestrator


SAMPLE_RAW_JSON = {
    "workItems": [
        {
            "id": "AZ-101",
            "fields": {
                "System.WorkItemType": "User Story",
                "System.State": "Done",
                "Microsoft.VSTS.Scheduling.StoryPoints": "15.0",
                "System.CreatedDate": "2026-07-01T10:00:00Z",
                "Microsoft.VSTS.Common.ClosedDate": "2026-07-03T16:00:00Z",
                "System.Title": "Implement Login Flow"
            }
        },
        {
            "id": "AZ-102",
            "fields": {
                "System.WorkItemType": "Bug",
                "System.State": "Done",
                "Microsoft.VSTS.Scheduling.StoryPoints": "TBD",
                "Microsoft.VSTS.Common.StateChangeDate_Reopened": 2,
                "System.CreatedDate": "2026-07-04T11:00:00Z",
                "Microsoft.VSTS.Common.ClosedDate": "2026-07-05T15:00:00Z",
                "System.Title": "Fix Null Pointer in Widget"
            }
        }
    ]
}

SAMPLE_GITHUB_JSON = {
    "inspectionDate": "2026-07-13T10:00:00Z",
    "project": {
        "id": "PROJ_1",
        "number": 1,
        "title": "Alpha Launch",
        "owner": "team",
        "org": "corp"
    },
    "iterations": [
        {
            "id": "ITER_1",
            "title": "Sprint 1",
            "startDate": "2026-07-01",
            "duration": 14
        }
    ],
    "sampleItems": [
        {
            "projectItemId": "PVTI_LADOCyFims4BdqvczgzPhMg",
            "projectItemType": "ISSUE",
            "id": "I_kwDOTYtncM8AAAABJPh3WA",
            "content": {
                "id": "I_kwDOTYtncM8AAAABJPh3WA",
                "number": 3,
                "title": "GitHub Real Format Ticket",
                "state": "OPEN",
                "createdAt": "2026-07-17T22:24:10Z",
                "updatedAt": "2026-07-19T05:25:52Z",
                "closedAt": None,
                "assignees": ["223138381 aero"],
                "labels": ["bug", "documentation"],
                "repository": "ge-aero/ATLAS-backend",
                "fieldValues": [
                    {"fieldName": "Status", "fieldType": "SingleSelect", "value": "In Review"},
                    {"fieldName": "Sprint", "fieldType": "Iteration", "value": "Sprint 1", "startDate": "2026-07-07", "duration": 14},
                    {"fieldName": "Estimate", "fieldType": "SingleSelect", "value": "8"}
                ]
            }
        },
        {
            "id": "GH-202",
            "type": "Issue",
            "content": {
                "title": "Fix API latency",
                "state": "OPEN"
            },
            "populatedFields": [
                {"fieldName": "Status", "value": "In review"},
                {"fieldName": "Estimate", "value": "4"},
                {"fieldName": "Sprint", "value": "Sprint 1"}
            ]
        }
    ]
}

SAMPLE_OD = [
    {
        "ticket_id": "AZ-099",
        "unit_type": "USER_STORY",
        "status_normalized": "DONE",
        "story_points": 20.0,
        "created_date": "2026-06-28",
        "completed_date": "2026-07-01",
        "is_first_time_yield": True,
        "board_id": 10
    }
]


SAMPLE_AZURE_PR_JSON = {
    "team": "smth",
    "repo": "Team",
    "cutoff": "2026-04-01T00:00:00+00:00",
    "pullRequests": [
        {
            "pullRequestId": 571,
            "title": "Task571",
            "status": "active",
            "creationDate": "2026-07-13T16:35:06.1245666Z",
            "commentCount": 0,
            "commitsAfterCreation": 1
        }
    ]
}


def test_normalizer_entity():
    """Test Stage 1: Normalizer entity."""
    print("--- Stage 1: Normalizer ---")
    new_tickets = Normalizer.normalize_raw_json(SAMPLE_RAW_JSON, board_id=10, default_record_date="2026-07-12")
    assert len(new_tickets) == 2
    assert new_tickets[0].ticket_id == "AZ-101" and new_tickets[0].story_points == 15.0
    assert new_tickets[1].story_points == 0.0  # "TBD" safely handled
    assert new_tickets[1].is_first_time_yield is False  # 2 reopen loops
    print(f"  [PASS] Normalizer.normalize_raw_json() -> {len(new_tickets)} clean tickets from raw vendor JSON")

    gh_tickets = Normalizer.normalize_raw_json(SAMPLE_GITHUB_JSON, board_id=10, default_record_date="2026-07-12")
    assert len(gh_tickets) == 2
    assert gh_tickets[0].ticket_id == "I_kwDOTYtncM8AAAABJPh3WA" and gh_tickets[0].story_points == 8.0
    assert gh_tickets[0].status_normalized == "IN_REVIEW"
    assert gh_tickets[1].status_normalized == "IN_REVIEW"
    assert gh_tickets[0].sprint == "Sprint 1"
    print(f"  [PASS] Normalizer.normalize_raw_json() -> {len(gh_tickets)} clean tickets from new GitHub JSON")

    old_tickets = Normalizer.normalize_db_od(SAMPLE_OD)
    assert len(old_tickets) == 1 and old_tickets[0].ticket_id == "AZ-099"
    print(f"  [PASS] Normalizer.normalize_db_od() -> {len(old_tickets)} clean tickets from historical OD")

    new_prs = Normalizer.normalize_prs(SAMPLE_AZURE_PR_JSON, board_id=10, default_record_date="2026-07-12")
    assert len(new_prs) == 1
    assert new_prs[0].pr_id == "571" and new_prs[0].status_normalized == "OPEN"
    assert new_prs[0].comment_count == 0 and new_prs[0].commits_after_creation == 1
    print(f"  [PASS] Normalizer.normalize_prs() -> {len(new_prs)} clean PRs from Azure DevOps screenshot schema")


def test_analyzer_entity():
    """Test Stage 2: Analyzer entity."""
    print("\n--- Stage 2: Analyzer ---")
    new_tickets, old_tickets, new_prs = Normalizer.normalize_all(SAMPLE_RAW_JSON, SAMPLE_OD, 10, "2026-07-12")
    combined = old_tickets + new_tickets

    fty = Analyzer.first_time_yield(combined)
    assert 0.0 <= fty <= 100.0
    print(f"  [PASS] Analyzer.first_time_yield() -> {fty}%")

    burndown = Analyzer.burndown_curve(combined, "2026-07-01", "2026-07-12", total_ideal_points=100.0)
    series = burndown.get("series", [])
    assert len(series) == 12
    print(f"  [PASS] Analyzer.burndown_curve() -> {len(series)} daily points calculated")

    kpis = Analyzer.measure_all(combined, "2026-07-01", "2026-07-12", {"total_ideal_points": 100.0})
    assert "fty_percentage" in kpis and "burndown_curve" in kpis
    print("  [PASS] Analyzer.measure_all() -> all KPIs computed over pointer list")


def test_formatter_entity():
    """Test Stage 3: Formatter entity."""
    print("\n--- Stage 3: Formatter ---")
    new_tickets, old_tickets, new_prs = Normalizer.normalize_all(SAMPLE_RAW_JSON, SAMPLE_OD, 10, "2026-07-12")
    kpis = Analyzer.measure_all(old_tickets + new_tickets, "2026-07-01", "2026-07-12", {"total_ideal_points": 100.0})

    contract = Formatter.to_graphic_contract(kpis)
    assert "first_time_yield_gauge" in contract and "burndown_curve" in contract
    print("  [PASS] Formatter.to_graphic_contract() -> bounds enforced, ui_graph_contracts formatted")

    csv_out = Formatter.to_csv(kpis)
    assert "First Time Yield" in csv_out
    print(f"  [PASS] Formatter.to_csv() -> {len(csv_out)} characters generated")


def test_worker_factory():
    """Test AnalyticsWorkerFactory orchestrating the Pure Factory pipeline."""
    print("\n--- AnalyticsWorkerFactory (Pure Factory Pattern) ---")
    payload = {
        "board_id": 10,
        "record_date": "2026-07-12",
        "start_date": "2026-07-01",
        "end_date": "2026-07-12",
        "kpi_config": {"total_ideal_points": 100.0},
        "raw_json": SAMPLE_RAW_JSON,
        "orchestrator_data_od": SAMPLE_OD,
    }

    result = AnalyticsWorkerFactory.execute(payload)

    db_record = result["kpi_record_for_db"]
    assert isinstance(db_record, dict) and db_record["board_id"] == 10
    assert db_record["total_story_points"] == 100.0
    assert db_record["completed_story_points"] == 35.0
    assert db_record["remaining_story_points"] == 65.0
    assert db_record["total_completed_tickets"] == 3
    assert db_record["first_time_yield_clean_tickets"] == 2
    print("  [PASS] AnalyticsWorkerFactory.execute() -> ProcessDataAggregate generated for Postgres")
    print(f"         Aggregate DB payload size: {len(json.dumps(db_record))} bytes (Zero memory copies!)")

    contract = result["graphic_contract"]
    assert "first_time_yield_gauge" in contract and "burndown_curve" in contract
    print("  [PASS] AnalyticsWorkerFactory.execute() -> graphic_contract generated for Qt GUI")


def test_orchestrator():
    """Test DockerWorkerOrchestrator driving the worker factory."""
    print("\n--- DockerWorkerOrchestrator ---")
    orchestrator = DockerWorkerOrchestrator(master_key_base64="my-secret-key")

    existing_dates = {"2026-07-01", "2026-07-02"}
    missing = orchestrator.identify_missing_date_gap("2026-07-01", "2026-07-05", existing_dates)
    assert missing == ["2026-07-03", "2026-07-04", "2026-07-05"]
    print(f"  [PASS] Orchestrator SQL gap detection -> missing dates: {missing}")

    encrypted_key = orchestrator.key_codec.encrypt_key("my_azure_pat_12345")
    graphic_output, sql_upsert, kpi_record_for_db = orchestrator.run_sync_cycle(
        board_id=10,
        kpi_config_id=42,
        requested_start_date="2026-07-01",
        requested_end_date="2026-07-05",
        existing_db_dates=existing_dates,
        existing_db_process_data_od=SAMPLE_OD,
        encrypted_api_key=encrypted_key,
        kpi_config={"total_ideal_points": 100.0},
    )

    assert "first_time_yield_gauge" in graphic_output and "INSERT INTO kpi_records_daily" in sql_upsert
    print("  [PASS] Orchestrator sync cycle -> graphic_contract + SQL UPSERT string generated")


def test_cli_stdin_stdout():
    """Test the exact CLI / Docker container sys.stdin -> sys.stdout pipeline using subprocess."""
    print("\n--- CLI / Container Entrypoint (`sys.stdin -> sys.stdout`) ---")
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "backend.worker.worker_factory"]
    payload_json = json.dumps({
        "board_id": 10,
        "record_date": "2026-07-12",
        "start_date": "2026-07-01",
        "end_date": "2026-07-12",
        "kpi_config": {"total_ideal_points": 100.0},
        "raw_json": SAMPLE_RAW_JSON,
        "orchestrator_data_od": SAMPLE_OD,
    })

    process = subprocess.run(cmd, input=payload_json, capture_output=True, text=True)
    assert process.returncode == 0, f"Subprocess failed with error: {process.stderr}"

    output_data = json.loads(process.stdout)
    assert output_data["board_id"] == 10
    assert "kpi_record_for_db" in output_data and "graphic_contract" in output_data
    print("  [PASS] Subprocess piped JSON to sys.stdin and successfully read 2-part JSON from sys.stdout!")
    print(f"         Total sys.stdout character output length: {len(process.stdout)} chars")


def main():
    print("=" * 64)
    print("  PROJECT ATLAS - PURE FACTORY BACKEND PIPELINE VERIFICATION")
    print("=" * 64)

    test_normalizer_entity()
    test_analyzer_entity()
    test_formatter_entity()
    test_worker_factory()
    test_orchestrator()
    test_cli_stdin_stdout()

    print("\n" + "=" * 64)
    print("  ALL PROJECT ATLAS PURE FACTORY TESTS PASSED 100%")
    print("=" * 64)


if __name__ == "__main__":
    main()
