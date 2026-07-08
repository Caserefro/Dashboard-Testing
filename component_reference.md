# WOR Dashboard — Graphic Component Reference

This document provides a complete technical specification for every SOLID graphic component in the WOR Dashboard architecture. It details the exact data models (inputs) required by each graph, chart, and table, along with copy-pasteable Python code examples showing how to instantiate them.

---

## Table of Contents
1. [SQDP KPI Boards (`SqdpBoardModel`)](#1-sqdp-kpi-boards)
2. [Threshold Bar Charts (`BarChartModel`)](#2-threshold-bar-charts)
3. [Progress Combo Charts (`ProgressBarChartModel`)](#3-progress-combo-charts)
4. [Burndown Curve Charts (`ProgressBarChartModel`)](#4-burndown-curve-charts)
5. [Pareto Loss Analysis Tables](#5-pareto-loss-analysis-tables)
6. [Safety Assessment Tables](#6-safety-assessment-tables)
7. [Dynamic Timeframe Selectors](#7-dynamic-timeframe-selectors)

---

## 1. SQDP KPI Boards

SQDP widgets render letter-grid diagrams (`S`, `Q`, `D`, `P`) where each cell represents a day or check-in period. Cells are color-coded: **Green** (on target) or **Red** (needs attention).

### Widgets Available
* `Sprint1WSqdpWidget` — 7 cells per letter (1-Week Sprint)
* `Sprint2WSqdpWidget` — 14 cells per letter (2-Week Sprint / Quarter)
* `DailySqdpWidget` — 31 cells per letter (Daily Calendar Month)

### Required Data Model: `SqdpBoardModel`
Located in `models/sqdp_models.py`.

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Display title rendered in the top card header. |
| `time_range` | `str` | Timeframe identifier: `"sprint_1w"`, `"sprint_2w"`, or `"daily"`. |
| `letters` | `List[SqdpLetterModel]` | Exactly 4 letter objects representing Safety, Quality, Delivery, and Productivity. |

#### Sub-Model: `SqdpLetterModel`
| Field | Type | Description |
|---|---|---|
| `char` | `str` | Single character identifier (`"S"`, `"Q"`, `"D"`, `"P"`). |
| `label` | `str` | Full category label (`"Safety"`, `"Quality"`, `"Delivery"`, `"Productivity"`). |
| `rows` | `int` | Height of the grid bounding box (in cells). |
| `cols` | `int` | Width of the grid bounding box (in cells). |
| `cells` | `List[Tuple[int, int]]` | List of `(row, col)` coordinates defining the letter shape. |
| `status` | `List[int]` | Parallel list of integer statuses (`1` = On Target/Green, `0` = Needs Attention/Red). |

### Example Definition
```python
from models.sqdp_models import SqdpLetterModel, SqdpBoardModel
from components.sqdp.sprint_1w_sqdp import Sprint1WSqdpWidget

# 1. Define coordinates forming the letter 'S' (5x3 grid, 7 cells for a 1-week sprint)
s_cells = [(0,0), (0,1), (0,2), (1,0), (2,1), (3,2), (4,0)]
s_status = [1, 1, 0, 1, 1, 1, 1]  # Day 3 missed safety target (0=Red)

# 2. Build letter models
letter_s = SqdpLetterModel(char="S", label="Safety", rows=5, cols=3, cells=s_cells, status=s_status)
letter_q = SqdpLetterModel(char="Q", label="Quality", rows=5, cols=3, cells=s_cells, status=[1]*7)
letter_d = SqdpLetterModel(char="D", label="Delivery", rows=5, cols=3, cells=s_cells, status=[1]*7)
letter_p = SqdpLetterModel(char="P", label="Productivity", rows=5, cols=3, cells=s_cells, status=[1]*7)

# 3. Create board model and instantiate widget
board_model = SqdpBoardModel(
    title="SQDP — Manufacturing Cell 4",
    time_range="sprint_1w",
    letters=[letter_s, letter_q, letter_d, letter_p]
)

sqdp_widget = Sprint1WSqdpWidget(board_model)
```

---

## 2. Threshold Bar Charts

Bar charts render vertical bars color-coded dynamically against threshold benchmarks: **Green** ($\ge$ green threshold), **Yellow** (between thresholds), or **Red** ($<$ red threshold).

### Widgets Available
* `SqdpBarChartWidget` — Standard efficiency/output bar chart.
* `SafetyBarChartWidget` — Stacked 4-metric safety chart (Incidents, Near Misses, Audits, Recordables).

### Required Data Model: `BarChartModel`
Located in `models/chart_models.py`.

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Chart header title. |
| `x_label` | `str` | Label rendered below the X-axis. |
| `categories` | `List[str]` | List of X-axis category names (e.g., `["Week 1", "Week 2", "Week 3"]`). |
| `values` | `List[float]` | Numeric bar values parallel to `categories`. |
| `green_threshold` | `float` | Benchmark value for green (target met). |
| `red_threshold` | `float` | Benchmark value for red (critical attention required). |
| `y_max` | `float` | Maximum scale for the Y-axis (default `1.0` for percentages, or custom like `100.0`). |

### Example Definition
```python
from models.chart_models import BarChartModel
from components.charts.sqdp_bar_chart import SqdpBarChartWidget

# 1. Define efficiency metrics across 5 weeks
chart_model = BarChartModel(
    title="Efficiency — Overall Equipment Effectiveness (OEE)",
    x_label="Sprint Week",
    categories=["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
    values=[88.5, 92.0, 74.2, 85.0, 95.5],
    green_threshold=85.0,  # >= 85% is Green
    red_threshold=75.0,    # < 75% is Red (Week 3 will render Red!)
    y_max=100.0
)

# 2. Instantiate widget
bar_chart_widget = SqdpBarChartWidget(chart_model)
```

---

## 3. Progress Combo Charts

Combines periodic vertical bars (e.g., weekly output counts) with two tracking lines: a solid line for cumulative actual progress and a dashed line for the cumulative target trajectory.

### Widget Available
* `ProgressBarChartWidget`

### Required Data Model: `ProgressBarChartModel`
Located in `models/chart_models.py`.

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Chart header title. |
| `x_label` | `str` | Label rendered below the X-axis. |
| `categories` | `List[str]` | List of X-axis time intervals. |
| `bar_values` | `List[float]` | Periodic output values (rendered as blue vertical bars). |
| `line_completed` | `List[float]` | Cumulative actual completed units (rendered as solid tracking line). |
| `line_total` | `List[float]` | Cumulative target trajectory (rendered as dashed benchmark line). |
| `y_max` | `float` | Maximum Y-axis scale limit. |

### Example Definition
```python
from models.chart_models import ProgressBarChartModel
from components.charts.progress_bar_chart import ProgressBarChartWidget

# 1. Define weekly production output vs cumulative sprint targets
progress_model = ProgressBarChartModel(
    title="Production Progress — Unit Assembly vs Target",
    x_label="Sprint Week",
    categories=["W1", "W2", "W3", "W4"],
    bar_values=[120.0, 135.0, 110.0, 140.0],       # Units produced each week
    line_completed=[120.0, 255.0, 365.0, 505.0],   # Cumulative actual
    line_total=[125.0, 250.0, 375.0, 500.0],       # Cumulative target
    y_max=600.0
)

# 2. Instantiate widget
progress_widget = ProgressBarChartWidget(progress_model)
```

---

## 4. Burndown Curve Charts

Tracks remaining backlog work across agile sprints or project milestones. Renders remaining points as vertical bars, actual burn trajectory as an orange curve, and ideal burndown as a dashed blue diagonal line.

### Widget Available
* `BurndownChartWidget`

### Required Data Model: `ProgressBarChartModel`
Uses the shared `ProgressBarChartModel` mapped to agile burndown metrics.

| Field | Type | How It Maps in Burndown Curve |
|---|---|---|
| `title` | `str` | Chart header title (e.g., `"Burndown Curve — Agile Delta Forecast"`). |
| `x_label` | `str` | X-axis label (e.g., `"Sprint Week"`). |
| `categories` | `List[str]` | Time intervals (e.g., `["Start", "W1", "W2", "W3", "W4"]`). |
| `bar_values` | `List[float]` | Remaining backlog points at each interval (rendered as bars). |
| `line_completed` | `List[float]` | Actual burn trajectory curve (solid orange line). |
| `line_total` | `List[float]` | Ideal burndown baseline (dashed blue line decreasing to 0). |
| `y_max` | `float` | Initial starting backlog points (top of scale). |

### Example Definition
```python
from models.chart_models import ProgressBarChartModel
from components.charts.burndown_chart import BurndownChartWidget

# 1. Define agile burndown across a 4-week sprint (starting at 200 points)
burndown_model = ProgressBarChartModel(
    title="Burndown Curve — Q3 Release Sprint",
    x_label="Sprint Milestone",
    categories=["Start", "Week 1", "Week 2", "Week 3", "Week 4"],
    bar_values=[200.0, 160.0, 110.0, 50.0, 0.0],     # Remaining points per week
    line_completed=[200.0, 160.0, 110.0, 50.0, 0.0], # Actual burn curve
    line_total=[200.0, 150.0, 100.0, 50.0, 0.0],     # Ideal diagonal burndown
    y_max=220.0
)

# 2. Instantiate widget
burndown_widget = BurndownChartWidget(burndown_model)
```

---

## 5. Pareto Loss Analysis Tables

Pareto tables track operational downtime, scrap rates, and root-cause incident logs across time periods.

### Widgets Available & Their Models
1. **`ParetoTable` & `ParetoTableUser`** ➔ Uses `ParetoTableModel`
2. **`ParetoTableAdmin`** (Yellow Theme) ➔ Uses `ParetoLogTableModel`
3. **`ParetoCategoryTable`** (2-Column Reference) ➔ Uses `ParetoCategoryTableModel`
4. **`ParetoTableCreate`** (3-Column Log without State) ➔ Uses `ParetoLogCreateTableModel`

### Required Data Models
Located in `models/table_models.py`.

#### A. `ParetoTableModel` (Grid Loss Analysis)
| Field | Type | Description |
|---|---|---|
| `title` | `str` | Table header title. |
| `categories` | `List[str]` | Row category labels (e.g., `["Machine Breakdown", "Setup Time"]`). |
| `columns` | `List[str]` | Column headers (e.g., `["W1", "W2", "W3"]`). |
| `values` | `List[List[float]]` | 2D matrix `[row][col]` of numeric loss hours/counts. |
| `averages` | `List[float]` | Row averages displayed in the rightmost summary column. |

#### B. `ParetoLogTableModel` (Admin Concern Log)
| Field | Type | Description |
|---|---|---|
| `title` | `str` | Table header title. |
| `entries` | `List[ParetoLogEntryModel]` | List of log entries. Each entry contains:<br>• `date: str` (`"07/07"`)<br>• `category: str`<br>• `comment: str`<br>• `state: str` (`"Open"`, `"In Progress"`, `"Resolved"`). |

#### C. `ParetoCategoryTableModel` (2-Column Reference)
| Field | Type | Description |
|---|---|---|
| `title` | `str` | Table header title. |
| `categories` | `List[ParetoCategoryEntryModel]` | List of categories. Each entry contains:<br>• `category: str` (Badge name)<br>• `description: str` (Definition/root cause explanation). |

#### D. `ParetoLogCreateTableModel` (3-Column Log without State)
| Field | Type | Description |
|---|---|---|
| `title` | `str` | Table header title. |
| `entries` | `List[ParetoLogCreateEntryModel]` | List of log entries. Each entry contains:<br>• `date: str`<br>• `category: str`<br>• `comment: str`. |

### Example Definitions
```python
from models.table_models import (
    ParetoTableModel, ParetoLogEntryModel, ParetoLogTableModel,
    ParetoCategoryEntryModel, ParetoCategoryTableModel
)
from components.tables.pareto.pareto_table import ParetoTable
from components.tables.pareto.pareto_table_admin import ParetoTableAdmin
from components.tables.pareto.pareto_category_table import ParetoCategoryTable

# ── Example 1: Grid Loss Analysis Table ──
grid_model = ParetoTableModel(
    title="Pareto Analysis — Weekly Downtime Hours",
    categories=["Machine Breakdown", "Setup & Changeover", "Material Shortage"],
    columns=["W1", "W2", "W3", "W4"],
    values=[
        [14.5, 12.0, 18.0, 10.5],
        [8.0,  9.5,  7.0,  8.5],
        [3.0,  2.0,  4.5,  1.0]
    ],
    averages=[13.75, 8.25, 2.63]
)
pareto_grid_widget = ParetoTable(grid_model)

# ── Example 2: Admin Concern Log (Yellow Theme) ──
log_entries = [
    ParetoLogEntryModel(date="07/05", category="Machine Breakdown", comment="CNC Spindle overheating", state="In Progress"),
    ParetoLogEntryModel(date="07/06", category="Material Shortage", comment="Late alloy delivery from vendor", state="Open")
]
admin_model = ParetoLogTableModel(title="Pareto Loss Audit Log", entries=log_entries)
pareto_admin_widget = ParetoTableAdmin(admin_model)

# ── Example 3: 2-Column Category Reference Table ──
cat_entries = [
    ParetoCategoryEntryModel(category="Machine Breakdown", description="Unplanned mechanical or electrical equipment failure > 15 mins."),
    ParetoCategoryEntryModel(category="Setup & Changeover", description="Time elapsed between last good part of run A and first good part of run B.")
]
cat_model = ParetoCategoryTableModel(title="Pareto Loss Category Definitions", categories=cat_entries)
pareto_category_widget = ParetoCategoryTable(cat_model)
```

---

## 6. Safety Assessment Tables

Safety tables display physiological ergonomics evaluations, OSHA compliance checklists, and weekly incident summaries.

### Widgets Available & Their Models
1. **`SafetyTable` & `SafetyAnswerWidget`** ➔ Uses `SafetyTableModel`
2. **`SafetyTableDashboard`** (Summary Table) ➔ Uses `SafetySummaryTableModel`

### Required Data Models
Located in `models/table_models.py`.

#### A. `SafetyTableModel` (Detailed Assessment & Questionnaire)
| Field | Type | Description |
|---|---|---|
| `title` | `str` | Table header title. |
| `principal` | `str` | Name of the safety officer or responsible person. |
| `categories` | `List[str]` | List of safety classification categories. |
| `fields` | `List[SafetyFieldModel]` | List of assessment fields. Each field contains:<br>• `field_name: str`<br>• `field_value: str` (`"Compliant"`, `"Action Required"`, etc.)<br>• `category: str`<br>• `comment: str`. |

#### B. `SafetySummaryTableModel` (Executive Summary Matrix)
| Field | Type | Description |
|---|---|---|
| `title` | `str` | Table header title. |
| `rows` | `List[SafetySummaryRowModel]` | List of weekly summaries. Each row contains:<br>• `week: str` (`"Week 1"`)<br>• `incidents: int`<br>• `near_misses: int`<br>• `safety_audits: int`<br>• `osha_recordables: int`. |

### Example Definitions
```python
from models.table_models import (
    SafetyFieldModel, SafetyTableModel,
    SafetySummaryRowModel, SafetySummaryTableModel
)
from components.tables.safety.safety_table import SafetyTable
from components.tables.safety.safety_table_dashboard import SafetyTableDashboard

# ── Example 1: Detailed Safety Assessment Table ──
safety_fields = [
    SafetyFieldModel(field_name="Ergonomic Station Posture", field_value="Compliant", category="Ergonomics", comment="All assembly height mats adjusted."),
    SafetyFieldModel(field_name="Chemical Eye Wash Station", field_value="Action Required", category="Chemical", comment="Inspection tag expired on Station 4.")
]
assessment_model = SafetyTableModel(
    title="Physiological Safety Assessment — Area B",
    principal="J. Doe (Safety Focal)",
    categories=["Ergonomics", "Chemical", "Mechanical"],
    fields=safety_fields
)
safety_table_widget = SafetyTable(assessment_model)

# ── Example 2: Executive Summary Matrix (Dashboard Table) ──
summary_rows = [
    SafetySummaryRowModel(week="Week 1", incidents=0, near_misses=2, safety_audits=5, osha_recordables=0),
    SafetySummaryRowModel(week="Week 2", incidents=1, near_misses=0, safety_audits=5, osha_recordables=0),
    SafetySummaryRowModel(week="Week 3", incidents=0, near_misses=1, safety_audits=6, osha_recordables=0)
]
summary_model = SafetySummaryTableModel(
    title="Safety Performance Summary (Last 3 Weeks)",
    rows=summary_rows
)
safety_summary_widget = SafetyTableDashboard(summary_model)
```

---

## 7. Dynamic Timeframe Selectors

The `DynamicSelectWidget` renders a clean selection bar with dynamic dropdown comboboxes for filtering dashboards by Timeframe, Team, Shift, or Metric.

### Widget Available
* `DynamicSelectWidget` (Located in `components/selection_widget.py`)

### Constructor Arguments
```python
DynamicSelectWidget(
    available_fields: Optional[Union[List[str], List[List[str]]]] = None,
    num_fields: int = 1,
    max_dropdowns: int = 5,
    show_count_selector: bool = False,
    title: Optional[str] = None,
    field_labels: Optional[List[str]] = None,
    parent: Optional[QWidget] = None
)
```

| Argument | Type | Default | Description |
|---|---|---|
| `available_fields` | `List[str]` or `List[List[str]]` | `None` (Default metrics) | Options to populate dropdowns. Pass a 1D list for identical dropdowns, or a 2D list `[ [opts1], [opts2] ]` for custom options per box. |
| `num_fields` | `int` | `1` | Number of dropdown boxes to render initially. |
| `show_count_selector` | `bool` | `False` | If `True`, renders an interactive "+ / -" selector allowing users to add/remove filter boxes dynamically. |
| `title` | `str` | `None` | Bold header title displayed at the left of the selection bar. |
| `field_labels` | `List[str]` | `None` | Custom labels rendered above/next to each dropdown box. |

### Example Definition
```python
from components.selection_widget import DynamicSelectWidget

# ── Example 1: Standard Timeframe & Shift Filter ──
filter_widget = DynamicSelectWidget(
    title="Global Dashboard Filter:",
    available_fields=[
        ["Current Sprint (Week 5)", "Previous Sprint (Week 4)", "Q3 Cumulative"],
        ["Shift 1 (Day)", "Shift 2 (Swing)", "Shift 3 (Graveyard)"]
    ],
    num_fields=2,
    show_count_selector=False
)

# ── Example 2: Interactive Multi-Metric Selector ──
metric_selector = DynamicSelectWidget(
    title="Compare KPIs:",
    available_fields=[
        "Safety — Ergonomics Assessment",
        "Quality — Scrap & Rework Rate",
        "Delivery — On-Time Delivery (OTD)",
        "Productivity — OEE"
    ],
    num_fields=3,
    show_count_selector=True  # Allows user to add up to 5 KPI dropdowns!
)
```
