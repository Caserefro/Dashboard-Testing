# GitHub Copilot Project Guide: Project ATLAS

## Overview
**Project ATLAS** is an Agile Analytics & Burndown Engine. It extracts live project items from GitHub Projects V2 (GraphQL) and Azure DevOps, normalizes vendor payloads into canonical domain data models, calculates advanced engineering KPIs (Method 3 PCHIP burndown interpolation), and formats outputs for CSV/Excel and Qt/Web dashboards.

---

## 4-Stage Pure Factory Architecture

1. **Stage 0: Extractor (`backend/worker/S0_Extractor/`)**:
   - `github_extractor.py`: GraphQL queries for items, PRs, and timeline events (`ISSUE_TIMELINE_QUERY`).
   - `timeline_parser.py`: Calculates stage cycle times (`time_in_todo_sec`, `time_in_progress_sec`, `time_in_review_sec`, `time_in_dev_testing_sec`, `time_in_rework_sec`). Clamps queue time to `sprint_start_date` if created before sprint start.
   - `utils.py`: `detect_sprint_window(work_items, record_date)` auto-detects active sprints matching `record_date`.

2. **Stage 1: Normalizer (`backend/worker/S1_Normalizer/`)**:
   - `base_mapper.py`: Normalizes statuses:
     - `DONE` / `CLOSED` / `RESOLVED` $\rightarrow$ `DONE`
     - `IN PROGRESS` / `DOING` $\rightarrow$ `IN_PROGRESS`
     - `IN REVIEW` / `REVIEW` $\rightarrow$ `IN_REVIEW`
     - `DEV TESTING` / `DEV_TESTING` $\rightarrow$ `DEV_TESTING` (its own category!)
     - `TODO` / `BACKLOG` $\rightarrow$ `TODO`

3. **Stage 2: Analyzer (`backend/worker/S2_Analyzer/`)**:
   - `burndown_math.py`: Method 3 PCHIP Monotonic Interpolation (`PchipInterpolator`) for Master Baseline, Catch-Up Track, and Slip Track.
   - `math_engines/time_math.py`: Active Engineering Cycle Time = `In Progress` + `In Review` + `Dev Testing` + `Rework`. `sprint_item_timeline` is strictly filtered to current active sprint items (`target_sprint`).

4. **Stage 3: Formatter (`backend/worker/S3_Formatter/`)**:
   - `csv_formatter.py`: Generates 30-column temporal CSV format.
   - `spreadsheet_formatter.py`: Generates graphic contracts for UI rendering.

---

## Corporate Proxy & Inspection

- SSL proxies are bypassed via `verify=ssl_verify` and `_resolve_ssl_verify()` in `http_utils.py`.
- Schema Inspector Command:
  ```powershell
  python backend/testing_tools/inspect_issue_schema.py --owner "YourOrg" --project 2 --no-ssl
  ```
- Master Pipeline Verification Command:
  ```powershell
  python -m backend.test_backend_pipeline
  ```
