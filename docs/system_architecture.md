# Project Documentation: Entities & Metrics

This document defines the primary architectural components (entities) that make up the system, as well as the dictionary of computed metrics (KPIs) supported by the backend pipeline.

---

## Part 1: System Architecture Entities

### 1. HTTP Handler
**Short Statement:** The entry point for all external web requests and API calls.
**Long Definition:** 
The HTTP Handler sits at the very edge of the system. Its sole responsibility is to receive incoming network requests (like REST API calls or webhooks), parse the incoming HTTP payload, validate basic schemas, and handle authentication/authorization. It acts as an adapter, completely isolating the underlying web framework (e.g., FastAPI, Flask) from the rest of the system. 

### 2. App Layer
**Short Statement:** The core business logic controller and use-case coordinator.
**Long Definition:** 
The Application Layer is the brain of the operation. It acts as the bridge between external interfaces (like HTTP Handlers or CLI commands) and the internal domain logic. It contains the core use cases of the application. When a request comes in, the App Layer coordinates the necessary steps to fulfill that request—such as requesting data from the Repository, triggering the Orchestrator, or invoking specific Workers.

### 3. Orchestrator
**Short Statement:** The workflow manager that schedules and sequences complex, multi-step operations.
**Long Definition:** 
The Orchestrator is responsible for managing the lifecycle of complex pipelines, such as data synchronization cycles or Docker CI/CD builds. It determines *how* a complex background process executes over time. It figures out what dates are missing (gap detection), sequences the Extraction and Analysis phases, handles retries, and oversees the complete end-to-end flow of data from extraction to database persistence.

### 4. Extractor
**Short Statement:** The external data integration module responsible for fetching raw data.
**Long Definition:** 
The Extractor (e.g., `github_extractor.py`) manages all direct communication with third-party systems and APIs (like GitHub's GraphQL API or Azure DevOps). It handles network timeouts, pagination, rate-limiting, and complex query construction, shielding the rest of the application from the volatility of third-party APIs.

### 5. Analyzer Worker (Pure Factory)
**Short Statement:** A stateless pipeline that transforms raw external data into computed metrics and presentation contracts.
**Long Definition:** 
The Analyzer Worker follows a Pure Factory pattern. It processes data through three distinct stages without any side effects:
*   **Normalizer (S1):** Maps chaotic, vendor-specific JSON into clean, canonical data models (e.g., `NormalizedTicket`).
*   **Analyzer (S2):** The heavy-lifting math engine that computes all business KPIs.
*   **Formatter (S3):** Shapes the computed KPIs into the final layout required by the consumer (e.g., horizontally stitched wide CSVs for Excel).

### 6. Repository
**Short Statement:** The data access layer that handles all database interactions.
**Long Definition:** 
The Repository pattern abstracts away all direct database mechanics (SQL queries, ORM sessions). It provides clean methods for the App Layer or Orchestrator to persist computed metrics or retrieve historical operational data.

---

## Part 2: Metrics Dictionary

The Analyzer (S2) engine currently supports the following advanced metrics, which are ultimately exported to the UI/Excel contracts.

### Velocity & Cycle Time Metrics
These metrics track the speed of delivery and identify bottlenecks in the pipeline.
*   **`TodoDays`**: The time (in days) a ticket spends sitting in the backlog after being created but before development starts.
*   **`InProgressDays`**: The active development time (clean time, excluding rework).
*   **`InReviewDays`**: The time a ticket spends undergoing peer review or QA.
*   **`ReworkDays`**: Time spent actively re-doing work after failing a review or being rejected. By tracking this separately, standard `InProgressDays` are not artificially inflated by poor quality.
*   **`TotalCycleDays`**: The total elapsed time from when work actually started (`InProgress`) to `Done`.
*   **`Average Time by Estimate (E2, E4, E8, E16)`**: Cycle times grouped and averaged by ticket complexity (Story Points). This allows teams to see if "8-point tickets" are taking disproportionately longer than expected.

### Quality & First Time Yield (FTY) Metrics
These metrics evaluate the quality of the work and the efficiency of the review processes.
*   **`Issue FTY (%)`**: The percentage of tickets that move smoothly from *Todo -> In Progress -> Review -> Done* without ever moving backwards on the board.
*   **`Avg Rework Loops`**: The average number of times tickets move backwards in the pipeline (e.g., from Review back to In Progress).
*   **`PR FTY (%)`**: The percentage of Pull Requests merged on the first pass (no "Changes Requested" reviews and no subsequent commits added after the PR was opened).
*   **`Avg Review Cycles`**: The average number of iteration loops a PR goes through before finally being merged.

### Forecasting & Burndown Metrics
These metrics power the "Method 3" advanced forecasting charts.
*   **`BurndownSP` (Live Actuals)**: The actual amount of story points remaining in the sprint as of the current date.
*   **`BurndownAVGSP` (Master Baseline)**: A smooth, mathematically interpolated curve (using PCHIP - Piecewise Cubic Hermite Interpolating Polynomial) derived from historical sprint performance. It represents the "ideal" path based on how the team *actually* works, rather than a straight line.
*   **`BurndownPredictionSP` (Catch-Up Track)**: An agile delta forecast. It calculates the current gap between the Actuals and the Baseline, and dynamically projects a curve that smoothly tapers that gap to zero by the sprint deadline.
*   **`SPDelta`**: The real-time gap (in story points) between where the team currently is, and where the Master Baseline says they should be.

### Volume Metrics
*   **`Total Story Points`**: Total complexity points committed to the sprint.
*   **`Bug SP` & `Non-Bug SP`**: The volume of work dedicated to fixing defects versus building features.
*   **`Clean SP (%)`**: The percentage of sprint capacity spent on feature work (`Non-Bug SP / Total Story Points`).
*   **State Counts**: Live counts of issues currently in `Todo`, `In Progress`, `Review`, and `Merged`.
