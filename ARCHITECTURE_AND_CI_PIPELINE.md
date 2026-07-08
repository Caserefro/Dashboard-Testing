# DMS Architecture & Immutable Docker CI Pipeline
**Project:** Daily Management System (DMS) / Dashboard Testing  
**Team:** LSE 2026 Team 2 - Systems Tools  
**Last Updated:** July 2026  

---

## Executive Summary
The Daily Management System (DMS) utilizes a **Layered Modular Architecture** that strictly decouples online data extraction, offline mathematical computation, and local GUI presentation. 

By enforcing an **Immutable Docker CI Gatekeeper** (`GraphContractValidator`), the system ensures that every metric calculation is rigorously verified offline before its container image (`analytics-worker:v1`) is baked. This guarantees **zero runtime validation overhead** inside the Qt 5 GUI and absolute data integrity inside the Postgres database.

---

## 1. End-to-End 3-Layer Architecture

Our system splits the data lifecycle into three distinct, secure boundaries:
1. **Online Raw Ingestion (Admin Controlled):** Network-enabled containers fetch 100% raw JSON payloads from Azure DevOps and GitHub Projects using OIDC authentication. End users never modify these containers.
2. **Offline Processing (Developer Sandboxed Worker):** A single unified Python container (`--network=none`, `--memory=512m`) loads raw JSON files, normalizes different vendor schemas into canonical models in RAM, computes KPIs (Burndown, First Time Yield, Velocity), and writes the final processed records directly to Postgres.
3. **Persistence & Presentation (Zero Overhead):** The local Qt 5 GUI queries the Postgres `processed_metrics` table and directly instantiates custom-drawn `QWidget` charts without runtime validation loops.

```mermaid
flowchart TB
    subgraph Layer1 ["1. Online Raw Ingestion Layer (Admin Managed / Network Enabled)"]
        OIDC["🔐 GE Authenticator (OIDC)"]
        subgraph Extractors ["Dockerized API Extractors"]
            Azure["📘 Azure DevOps API Connector"]
            GitHub["🐙 GitHub Projects API Connector"]
        end
        OIDC -.-> Azure & GitHub
        Azure & GitHub -->|1. Dump 100% Raw JSON Blobs| RawStore[(📂 Raw JSON Data Volume)]
    end

    subgraph Layer2 ["2. Offline Processing Layer (Developer Sandboxed Worker)"]
        RawStore -->|2. Read Raw Files| Worker["🐍 Unified Analytics Worker Container<br>docker run --network=none --memory=512m"]
        
        subgraph Internal_Python ["Inside Python Worker Process"]
            Worker -->|3. Normalize in RAM| Models["Canonical Data Models<br>(Tickets, Story Points, PRs)"]
            Models -->|4. Compute KPIs in RAM| KPIs["Metric Math Engine<br>(Burndown, FTY, Velocity)"]
        end
    end

    subgraph Layer3 ["3. Persistence & Presentation Layer (Zero Overhead)"]
        KPIs -->|5. Write Pre-Validated Rows| DB[(🗄️ Postgres ERD Database<br>processed_metrics Table)]
        DB -->|6. Fast Direct Query| GUI["🖥️ Local Qt 5 Dashboard<br>(Burndown, Gauges, Bar Charts)"]
    end

    style Extractors fill:#1565c0,color:#fff,stroke:#0d47a1,stroke-width:2px
    style Worker fill:#2e7d32,color:#fff,stroke:#1b5e20,stroke-width:2px
    style DB fill:#0277bd,color:#fff,stroke:#01579b,stroke-width:2px
    style GUI fill:#283593,color:#fff,stroke:#1a237e,stroke-width:2px
```

---

## 2. The Immutable Docker CI Gatekeeper

We do not test or validate schemas dynamically inside the Qt GUI widgets on every load. Instead, we follow the **"Test ONCE at the Gate -> Bake Immutable Image"** design pattern.

When a developer adds a new KPI calculation (`compute_new_metric.py`), our automated CI pipeline executes `test_ci_contracts.py` alongside `GraphContractValidator`. It checks the output against `config/ui_graph_contracts.json`. If the output matches exact field names and numeric bounds (`min_value: 0.0, max_value: 100.0`), the Docker image (`analytics-worker:v1`) is created. If it fails, the build is aborted immediately.

```mermaid
flowchart LR
    subgraph CI_Stage ["Continuous Integration (CI) Stage — Before Image Creation"]
        Code["🐍 New / Updated KPI Python Code"]
        Fixtures["📂 Raw JSON Sample Fixtures"]
        Contract["📄 config/ui_graph_contracts.json<br>(Single Source of Truth)"]
        
        Code & Fixtures & Contract --> Gate["⚙️ test_ci_contracts.py<br>(GraphContractValidator Engine)"]
        Gate --> Check{"Does Python output exactly<br>match UI & DB schema?"}
        
        Check -->|NO: Bad Type or Out of Bounds| Abort["❌ CI ABORTED<br>(No Docker Image Created)"]
        Check -->|YES: 100% Validated| Build["📦 docker build -t analytics-worker:v1<br>(Bake Immutable Container Snapshot)"]
    end

    subgraph Prod_Stage ["Production Runtime"]
        Build -->|Deploy Snapshot| Runtime["🚀 Production Container Runs<br>Guaranteed Deterministic Output!"]
    end

    style Gate fill:#e65100,color:#fff,stroke:#bf360c,stroke-width:2px
    style Build fill:#2e7d32,color:#fff,stroke:#1b5e20,stroke-width:2px
    style Abort fill:#c62828,color:#fff,stroke:#b71c1c,stroke-width:2px
```

---

## 3. Pure Direct Qt GUI Rendering Flow

Because the CI Gatekeeper guarantees that no invalid data can ever be written by `analytics-worker:v1`, the presentation layer (`contract_graph_harness.py`) operates with complete confidence and maximum speed. 

When `create_graph_widget_from_data(graph_key, raw_data)` is called, it directly passes database records into high-performance, antialiased custom widgets (`FirstTimeYieldGaugeWidget`, `ContractBarChartWidget`).

```mermaid
flowchart LR
    subgraph DB_Layer ["Postgres Database"]
        DB[(🗄️ processed_metrics Table)]
    end

    subgraph Qt_Presentation ["Qt 5 GUI Presentation Layer (contract_graph_harness.py)"]
        DB -->|1. SELECT * WHERE graph='fty_gauge'| Query["QSqlDatabase / MetricRepository"]
        Query -->|2. Pass Raw Records Directly| Factory["create_graph_widget_from_data()"]
        
        Factory -->|If fty_gauge| W1["FirstTimeYieldGaugeWidget<br>(Antialiased QPainter Radial Arc)"]
        Factory -->|If burndown_curve| W2["ContractBarChartWidget<br>(Custom Bar Chart Canvas)"]
    end

    style Factory fill:#4527a0,color:#fff,stroke:#311b92,stroke-width:2px
    style W1 fill:#00e676,color:#000,stroke:#00c853,stroke-width:2px
    style W2 fill:#2979ff,color:#fff,stroke:#1565c0,stroke-width:2px
```

---

## 4. The 3 Golden Contracts

To add new features or KPI plugins in minutes without breaking existing workflows, all components must adhere to three core contracts:

### A. Input Contract (`test_fixtures/`)
Static snapshot JSON files representing real raw outputs from Azure DevOps (`raw_azure_sample.json`) and GitHub Projects (`raw_github_sample.json`). These provide deterministic inputs for local testing and CI verification.

### B. UI Graph Contract (`config/ui_graph_contracts.json`)
The single source of truth defining exact required fields, data types, and value bounds for each Qt graph.
```json
{
  "graphs": {
    "burndown_curve": {
      "type": "xy_line_chart",
      "required_fields": [
        { "name": "date", "type": "string_iso8601" },
        { "name": "remaining_points", "type": "float", "min_value": 0.0 },
        { "name": "ideal_points", "type": "float", "min_value": 0.0 }
      ]
    },
    "first_time_yield_gauge": {
      "type": "gauge",
      "required_fields": [
        { "name": "fty_percentage", "type": "float", "min_value": 0.0, "max_value": 100.0 }
      ]
    }
  }
}
```

### C. DB Schema Contract (`processed_metrics` Table)
The relational schema in Postgres where the Python analytics worker inserts final metric rows:
* `ticket_id` (VARCHAR NOT NULL)
* `metric_name` (VARCHAR NOT NULL)
* `metric_value` (FLOAT NOT NULL)
* `category_label` (VARCHAR)
* `timestamp` (TIMESTAMPTZ NOT NULL)

---

## 5. Developer Workflow: Adding a New KPI Plugin

To implement a new dashboard graph or metric (e.g., **Code Review Turnaround Time**):
1. **Define the Requirement:** Add the expected graph schema to `config/ui_graph_contracts.json`.
2. **Write the Math:** Create `compute_cr_turnaround(tickets: List[Ticket]) -> Dict[str, Any]` inside the unified Python analytics worker code.
3. **Run CI Verification:** Run `python test_ci_contracts.py`. The script feeds sample raw JSON to your function and validates the output against `ui_graph_contracts.json`.
4. **Bake & Deploy:** Once CI passes `[SUCCESS]`, run `docker build -t analytics-worker:latest .`. The new metric is now live and ready to be consumed by the Qt GUI with zero runtime harness overhead!
