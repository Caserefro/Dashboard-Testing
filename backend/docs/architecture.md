# Project ATLAS - Backend Architecture

## Core Philosophy: SOLID & Pure Factory
The backend is designed entirely around the **Pure Factory Pattern** and **Domain-Driven Design (DDD)**. 

Our main priority is keeping the core mathematical analytics (the `Domain`) completely isolated from the database (the `Infrastructure`), and executing pipeline workloads cleanly in RAM with zero network-waits or pickling/serialization copies during the crunch phases.

## Directory Structure

```text
backend/
├── application_layer.py   <-- Business Logic Coordinator (The Boss)
├── dependencies.py        <-- Fast API / DI Wiring
├── domain/                <-- Entities & Models (e.g. NormalizedTicket, ProcessDataAggregate)
├── orchestrator/          <-- Facade (Spawns S0 extractors, packages data for S1-3)
├── publisher/             <-- Asynchronous Workers that push outputs to frontends (Smartsheet)
├── repository/            <-- Infrastructure layer (Data at Rest, API Key Crypto, Postgres)
└── worker/
    ├── S0_Extractor/      <-- API specific integrations (GitHub, Azure)
    ├── S1_Normalizer/     <-- Cleans vendor JSON into our Domain entities
    ├── S2_Analyzer/       <-- The Math (Burndown, First Time Yield, PCHIP Interpolation)
    ├── S3_Formatter/      <-- Bounds-checking and formatting for outputs (Graphic Contract, CSV)
    └── worker_factory.py  <-- The script that runs S1->S2->S3 in RAM in sub-milliseconds
```

## The Pipeline Flow (S0 -> S1 -> S2 -> S3)

1. **The Request:** `application_layer.py` receives a trigger (HTTP or cron). It asks `repository/` for the decrypted API keys and the existing baseline data (`Orchestrator Data` / `OD`).
2. **S0 Extractor (I/O Bound):** The Orchestrator spawns the GitHub/Azure extractors in isolated subprocesses using standard `sys.stdin`/`sys.stdout` pipes. They fetch *only* the missing dates from the vendor APIs and return raw JSON.
3. **The Pure Factory Worker (CPU Bound):** The Orchestrator feeds the raw JSON + historical OD into `worker_factory.py`. This script executes entirely in RAM without network access:
   - **S1 (Normalizer):** Converts raw JSON into pure `NormalizedTicket` python objects.
   - **S2 (Analyzer):** Runs `burndown_math` (PCHIP interpolation), FTY calculations, and velocity mapping.
   - **S3 (Formatter):** Packages everything safely into the `graphic_contract`.
4. **Persistence:** The Orchestrator returns the new baseline (`kpi_record_for_db`) which the `application_layer` saves back to `repository`.
5. **Publishing:** The `application_layer` spawns the `publisher/smartsheet_publisher.py` in the background (fire-and-forget) to push the `graphic_contract` up to the Smartsheet frontend without blocking the HTTP caller.

## Mermaid Flow Diagram

```mermaid
graph TD
    Trigger[HTTP / Cron Trigger] --> Boss(application_layer.py)
    Boss -- "1. Get API Keys & OD" --> Repo[(Repository/Postgres)]
    Boss -- "2. Start Sync Cycle" --> Orch[Orchestrator]
    
    Orch -- "3. Missing Dates Only" --> S0[S0_Extractor]
    S0 -- "Raw JSON" --> Orch
    
    Orch -- "4. Raw JSON + OD" --> Factory((Worker Factory))
    
    subgraph RAM Execution (< 5ms)
        Factory --> S1[S1_Normalizer]
        S1 --> S2[S2_Analyzer Math]
        S2 --> S3[S3_Formatter]
    end
    
    S3 -- "graphic_contract + new OD" --> Orch
    Orch --> Boss
    
    Boss -- "5. Fire-and-Forget" --> Pub[Smartsheet Publisher]
    Pub -- "Async Write" --> Smartsheet[(Smartsheet API)]
    
    Boss -- "6. Save Baseline" --> Repo
```
