---
name: project-atlas-board-adapter
description: >-
  Adapts Project ATLAS mappers, extractors, and status normalizers to any new corporate
  GitHub Projects V2 or Azure DevOps board schema (e.g. Dev Testing, custom sprint names).
---

# Project ATLAS Board Adapter Skill

## Overview
This skill guides GitHub Copilot and AI assistants through inspecting a new project board's GraphQL schema, updating status mappers, configuring sprint window detection, and running pipeline verification tests.

---

## Technical Protocol

### Step 1: Inspect Target Board Schema
Run the schema inspector tool to extract custom statuses, iteration windows, and story point estimate fields:
```powershell
python backend/testing_tools/inspect_issue_schema.py --owner "CorporateOrg" --project <PROJECT_NUMBER> --no-ssl
```

### Step 2: Configure Status Mappers
1. Update `backend/worker/S1_Normalizer/mappers/base_mapper.py`:
   - Map custom status strings to canonical categories (`IN_PROGRESS`, `IN_REVIEW`, `DEV_TESTING`, `DONE`, `TODO`).
2. Update `backend/worker/S0_Extractor/github/timeline_parser.py`:
   - Add status strings to `STATUS_MAP` (e.g., `"dev testing": "DevTesting"`).

### Step 3: Verify Sprint Iterations
1. Verify `detect_sprint_window(work_items, record_date)` in `backend/worker/S0_Extractor/github/utils.py`.
2. Ensure sprint windows formatted as `"WE MM-DD-YYYY"` or custom strings match `start_date <= record_date <= end_date`.

### Step 4: Run Verification Tests
Run the master test suite to verify 100% test pass:
```powershell
python -m backend.test_backend_pipeline
```
