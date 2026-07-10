"""
Component Gallery - Interactive Storybook for WOR Dashboard Components
======================================================================

A standalone testing harness (similar to Jetpack Compose Previews or
Storybook) that lets you select and preview any graphic component
in isolation with mock data.

Usage:
    python tools/component_gallery.py

Features:
    - Left sidebar listing all available graphic components
    - Main preview canvas rendering the selected component
    - "Randomize Data" button to test dynamic data updates
    - Components organized by family: SQDP, Charts, Tables
"""

import sys
import os
import random
import numpy as np
from scipy.interpolate import PchipInterpolator

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QStackedWidget,
    QSplitter, QFrame,
)
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QSize

# ── Models ──
from models.sqdp_models import SqdpLetterModel, SqdpBoardModel
from models.chart_models import BarChartModel, ProgressBarChartModel, BurndownChartModel, SafetyBarChartModel
from models.table_models import (
    ParetoTableModel,
    ParetoLogEntryModel,
    ParetoLogTableModel,
    ParetoCategoryEntryModel,
    ParetoCategoryTableModel,
    ParetoLogCreateEntryModel,
    ParetoLogCreateTableModel,
    SafetyTableModel,
    SafetySummaryTableModel,
    SafetyFieldModel,
    TextGuideTableModel,
    TextGuideColumnModel,
    SafetyQuestionModel,
    SafetyQuestionnaireModel,
)

# ── Components ──
from components.sqdp.sprint_1w_sqdp import Sprint1WSqdpWidget
from components.sqdp.sprint_2w_sqdp import Sprint2WSqdpWidget
from components.sqdp.daily_sqdp import DailySqdpWidget
from components.sqdp.sqdp_board_widget import SqdpBoardWidget
from components.charts.sqdp_bar_chart import SqdpBarChartWidget
from components.charts.progress_bar_chart import ProgressBarChartWidget
from components.charts.burndown_chart import BurndownChartWidget
from components.charts.safety_bar_chart import SafetyBarChartWidget, StackedSafetyBarChart
from components.tables.pareto.pareto_table import ParetoTable
from components.tables.pareto.pareto_table_user import ParetoTableUser
from components.tables.pareto.pareto_table_admin import ParetoTableAdmin
from components.tables.pareto.pareto_category_table import ParetoCategoryTable
from components.tables.pareto.pareto_table_create import ParetoTableCreate
from components.tables.safety.safety_table import SafetyTable
from components.tables.safety.safety_table_dashboard import SafetyTableDashboard
from components.tables.safety.safety_table_admin import SafetyTableAdmin
from components.tables.safety.safety_question_widget import SafetyAnswerWidget, SafetyQuestionWidget, SafetyQuestionnaireWidget
from components.tables.guide_table import TextGuideTable, SafetyGuideTable, ParetoTableGuide
from components.selection_widget import DynamicSelectWidget
from components.dashboard_grid import ScrollableDashboardGrid


# ══════════════════════════════════════════════════════════════
# MOCK DATA GENERATORS (Delegating to Service-Repository Layer)
# ══════════════════════════════════════════════════════════════

from repositories.mock.mock_sqdp_repository import MockSqdpRepository
from repositories.mock.mock_chart_repository import MockChartRepository
from repositories.mock.mock_table_repository import MockTableRepository
from services.sqdp_service import SqdpService
from services.chart_service import ChartService
from services.table_service import TableService

# Singleton service instances with injected repositories for testing
_sqdp_service = SqdpService(MockSqdpRepository())
_chart_service = ChartService(MockChartRepository())
_table_service = TableService(MockTableRepository())


def generate_sqdp_board(time_range: str) -> SqdpBoardModel:
    """Generate a complete SQDP board using the Service-Repository layer."""
    return _sqdp_service.get_processed_data(time_range=time_range)


def generate_bar_chart() -> BarChartModel:
    """Generate a bar chart model using the Service-Repository layer."""
    return _chart_service.get_processed_data(chart_type="bar")


def generate_progress_chart() -> ProgressBarChartModel:
    """Generate a progress combo chart using the Service-Repository layer."""
    return _chart_service.get_processed_data(chart_type="progress")


def generate_pareto_table() -> ParetoTableModel:
    """Generate a Pareto table using the Service-Repository layer."""
    return _table_service.get_processed_data(table_type="pareto")


def generate_pareto_admin_table() -> ParetoLogTableModel:
    """Generate an Admin Pareto Loss Log table with Date/Category/State/Comment and Inputs/Outputs."""
    return ParetoLogTableModel(
        title="Pareto Loss Admin Log",
        principal="Line Admin Review",
        entries=[
            ParetoLogEntryModel(date="07/01", category="Machine Breakdown", state="Resolved", comment="Conveyor belt jammed on Line 2; maintenance replaced bearing.", inputs="500 units", outputs="420 units"),
            ParetoLogEntryModel(date="07/02", category="Lack of Materials", state="In Progress", comment="Late delivery of packaging film from supplier.", inputs="500 units", outputs="450 units"),
            ParetoLogEntryModel(date="07/03", category="Quality Defect", state="Open", comment="Seal temperature drift caused rejected pouches.", inputs="520 units", outputs="480 units"),
            ParetoLogEntryModel(date="07/04", category="Operator Error", state="Resolved", comment="Misaligned sensor during shift changeover.", inputs="500 units", outputs="465 units"),
            ParetoLogEntryModel(date="07/05", category="Machine Breakdown", state="Open", comment="Hydraulic pressure drop on stamping press.", inputs="500 units", outputs="410 units"),
        ],
    )


def generate_pareto_category_table() -> ParetoCategoryTableModel:
    """Generate a Pareto category reference table with 2 columns (Category & Description)."""
    return ParetoCategoryTableModel(
        title="Pareto Loss Categories & Definitions",
        entries=[
            ParetoCategoryEntryModel("Machine Breakdown", "Unplanned mechanical or electrical equipment failure halting production line."),
            ParetoCategoryEntryModel("Lack of Materials", "Production delay caused by missing raw materials or component stock-outs."),
            ParetoCategoryEntryModel("Quality Defect", "Rejected units, out-of-spec packaging, or seal integrity failures."),
            ParetoCategoryEntryModel("Operator Error", "Process disruption resulting from incorrect setup or procedural deviation."),
            ParetoCategoryEntryModel("Planned Maintenance", "Scheduled preventative maintenance or tooling changeover."),
        ],
    )


def generate_pareto_create_table() -> ParetoLogCreateTableModel:
    """Generate a Pareto loss creation table (without State column, filled by text)."""
    return ParetoLogCreateTableModel(
        title="Pareto Loss Creation Log",
        principal="Shift Operator Input",
        entries=[
            ParetoLogCreateEntryModel("07/07", "Machine Breakdown", "Conveyor belt jammed on Line 2 during morning startup."),
            ParetoLogCreateEntryModel("07/07", "Lack of Materials", "Waiting 25 minutes for secondary carton packaging delivery."),
            ParetoLogCreateEntryModel("07/07", "Quality Defect", "Top seal misaligned on 15 consecutive pouches."),
            ParetoLogCreateEntryModel("07/07", "Operator Error", "Sensor calibration knocked out of alignment during cleaning."),
        ],
    )


def generate_safety_table() -> SafetyTableModel:
    """Generate a safety table using the Service-Repository layer."""
    return _table_service.get_processed_data(table_type="safety")


def generate_safety_summary_table() -> SafetySummaryTableModel:
    """Generate the Week 5 summary dashboard table matching Image 1."""
    return SafetySummaryTableModel(
        period_title="Week 5",
        headers=["# No responses", "Motivation Average", "Connection Average", "Workload Average", "Teamwork Average", "Total Average"],
        values=["0", "3.0", "2.7", "3.3", "3.3", "3.1"],
        total_index=5,
        target_threshold=2.5,
    )


def generate_safety_guide_table() -> TextGuideTableModel:
    """Generate the Psychological Safety Metric reference guide matrix."""
    return TextGuideTableModel(
        title="Psychological Safety Metric",
        row_label_header="",
        columns=[
            TextGuideColumnModel(header="1", color="#D32F2F"),  # Red
            TextGuideColumnModel(header="2", color="#EF6C00"),  # Orange/Amber
            TextGuideColumnModel(header="3", color="#2E7D32"),  # Green
            TextGuideColumnModel(header="4", color="#1565C0"),  # Blue
        ],
        row_labels=[
            "Motivation",
            "Connected",
            "Workload",
            "Teamwork",
        ],
        matrix=[
            [
                "Disengaged",
                "Lack of Motivation",
                "Motivated",
                "Energised",
            ],
            [
                "Isolated",
                "Not feeling heard",
                "Listened To",
                "Strong sense of Belonging",
            ],
            [
                "Continually overwhelmed / Bored",
                "Momentarily overwhelmed",
                "Managing Workload",
                "Optimum Workload",
            ],
            [
                "Major conflicts ongoing",
                "Team Disagreements",
                "Positive Discussions",
                "Healthy Conflict",
            ],
        ],
    )


def generate_burndown_chart() -> BurndownChartModel:
    """Generate burndown curve model using the Service-Repository layer."""
    return _chart_service.get_processed_data(chart_type="burndown")


def generate_safety_bar_chart() -> SafetyBarChartModel:
    """Generate mock stacked safety SQDP bar chart model."""
    import random
    categories = [str(i) for i in range(1, 14)]  # Weeks 1..13
    sub_values = [
        [0.75, 0.50, 0.75, 0.80],  # W1: 2.80 (>=2.5 Green)
        [0.80, 0.50, 0.75, 0.75],  # W2: 2.80 (>=2.5 Green)
        [0.50, 0.50, 0.75, 0.75],  # W3: 2.50 (>=2.5 Green)
        [0.25, 0.50, 0.75, 0.75],  # W4: 2.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.20],  # W5: 2.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.20],  # W6: 2.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.20],  # W7: 2.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.20],  # W8: 2.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.20],  # W9: 2.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.20],  # W10: 2.25 (<2.5 Red)
        [0.30, 0.50, 0.25, 0.20],  # W11: 1.25 (<2.5 Red)
        [0.80, 0.50, 0.75, 0.70],  # W12: 2.75 (>=2.5 Green)
        [0.80, 0.50, 0.75, 0.70],  # W13: 2.75 (>=2.5 Green)
    ]
    return SafetyBarChartModel(
        title="Safety Assessment: Weekly SQDP Breakdown",
        x_label="Weeks",
        categories=categories,
        sub_values=sub_values,
        target_threshold=2.5,
        y_max=3.0,
    )


def generate_safety_questionnaire(already_filled: bool = False) -> SafetyQuestionnaireModel:
    """Generate mock interactive safety assessment questionnaire model."""
    return SafetyQuestionnaireModel(
        title="Psychological Safety Assessment Questionnaire",
        already_filled=already_filled,
        completed_message="Thank you! This safety assessment has already been filled and submitted for the current period.",
        questions=[
            SafetyQuestionModel(
                prompt_text="Motivation: Disengaged / Lack of Motivation / Motivated / Energised",
                options=["Disengaged", "Lack of Motivation", "Motivated", "Energised"],
                selected_option="Motivated",
            ),
            SafetyQuestionModel(
                prompt_text="Connected: Isolated / Not feeling heard / Listened To / Strong sense of Belonging",
                options=["Isolated", "Not feeling heard", "Listened To", "Strong sense of Belonging"],
                selected_option="Listened To",
            ),
            SafetyQuestionModel(
                prompt_text="Workload: Continually overwhelmed / Bored / Managing Workload / Optimum Workload",
                options=["Continually overwhelmed", "Bored", "Managing Workload", "Optimum Workload"],
                selected_option="Managing Workload",
            ),
            SafetyQuestionModel(
                prompt_text="Teamwork: Major conflicts ongoing / Team Disagreements / Positive Discussions / Healthy Conflict",
                options=["Major conflicts ongoing", "Team Disagreements", "Positive Discussions", "Healthy Conflict"],
                selected_option="Positive Discussions",
            ),
        ],
    )


def create_demo_grid() -> ScrollableDashboardGrid:
    """Create a sample 2-column scrollable dashboard grid for gallery preview."""
    grid = ScrollableDashboardGrid(columns=2)
    grid.add_widget(DynamicSelectWidget(num_fields=2, show_count_selector=True), row=0, col=0, col_span=2, min_height=85)
    grid.add_widget(Sprint1WSqdpWidget(generate_sqdp_board("sprint_1w")), row=1, col=0, col_span=2, min_height=260)
    grid.add_widget(BurndownChartWidget(generate_burndown_chart()), row=2, col=0, min_height=380)
    grid.add_widget(SqdpBarChartWidget(generate_bar_chart()), row=2, col=1, min_height=380)
    grid.add_widget(ParetoTable(generate_pareto_table()), row=3, col=0, col_span=2, min_height=350)
    return grid


# ══════════════════════════════════════════════════════════════
# COMPONENT REGISTRY
# ══════════════════════════════════════════════════════════════

COMPONENT_REGISTRY = [
    # (display_name, icon_emoji, factory_function)
    # ── SQDP Family ──
    ("SQDP Unified Board Widget (Dynamic 13/31-cell)", "sqdp", lambda: SqdpBoardWidget(generate_sqdp_board("daily"))),
    ("SQDP Sprint 1 Week",    "sqdp",  lambda: Sprint1WSqdpWidget(generate_sqdp_board("sprint_1w"))),
    ("SQDP Sprints / Quarter (13 Weeks)", "sqdp", lambda: Sprint2WSqdpWidget(generate_sqdp_board("sprint_2w"))),
    ("SQDP Daily (31 cells)", "sqdp",  lambda: DailySqdpWidget(generate_sqdp_board("daily"))),
    # ── Charts Family ──
    ("Bar Chart (Efficiency)", "chart", lambda: SqdpBarChartWidget(generate_bar_chart())),
    ("Progress Combo Chart",   "chart", lambda: ProgressBarChartWidget(generate_progress_chart())),
    ("Burndown Curve Forecast (Agile Delta)", "chart", lambda: BurndownChartWidget(generate_burndown_chart())),
    ("Safety SQDP Bar Chart (Stacked 4-Metric)", "chart", lambda: SafetyBarChartWidget(generate_safety_bar_chart())),
    # ── Pareto Tables ──
    ("Pareto Table (Dashboard)", "table", lambda: ParetoTable(generate_pareto_table())),
    ("Pareto Table (User)",      "table", lambda: ParetoTableUser(generate_pareto_table())),
    ("Pareto Table (Admin Loss Log - Yellow Theme)", "table", lambda: ParetoTableAdmin(generate_pareto_admin_table())),
    ("Pareto Category Table (2-Column Reference)", "table", lambda: ParetoCategoryTable(generate_pareto_category_table())),
    ("Pareto Table Create (Loss Log - Without State)", "table", lambda: ParetoTableCreate(generate_pareto_create_table())),
    # ── Safety Tables ──
    ("Safety Table (Dashboard Summary - Week 5)", "table", lambda: SafetyTableDashboard(generate_safety_summary_table())),
    ("Safety Table (Admin Concern Log - Yellow Theme)", "table", lambda: SafetyTableAdmin(generate_safety_table())),
    ("Safety Table (Detailed Log - Old Standard View)", "table", lambda: SafetyTable(generate_safety_table())),
    ("Text Guide Table (Safety Metric Matrix)", "table", lambda: TextGuideTable(generate_safety_guide_table())),
    ("Safety Answer Widget (Active Questionnaire)", "table", lambda: SafetyAnswerWidget(generate_safety_questionnaire(False))),
    ("Safety Answer Widget (Already Submitted State)", "table", lambda: SafetyAnswerWidget(generate_safety_questionnaire(True))),
    # ── Controls & Selectors ──
    ("Selection Bar (Production: Fixed Count)", "control", lambda: DynamicSelectWidget(num_fields=2, show_count_selector=False)),
    ("Selection Bar (Demo: Interactive Count)", "control", lambda: DynamicSelectWidget(num_fields=3, show_count_selector=True)),
    # ── Layouts & Grids ──
    ("Scrollable Dashboard Grid (2x2 Demo)", "layout", lambda: create_demo_grid()),
]


# ══════════════════════════════════════════════════════════════
# GALLERY WINDOW
# ══════════════════════════════════════════════════════════════

class ComponentGallery(QMainWindow):
    """Interactive storybook for previewing WOR Dashboard components.

    Provides a sidebar navigation listing all registered graphic
    components. Selecting one loads it into the main preview area
    with freshly generated mock data.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Component Gallery - WOR Dashboard")
        self.resize(1200, 700)
        self.setStyleSheet("""
            QMainWindow { background: #ECEFF1; }
            QListWidget {
                background: #263238;
                color: #ECEFF1;
                border: none;
                font-size: 13px;
                font-family: 'Segoe UI';
                outline: none;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #37474F;
            }
            QListWidget::item:selected {
                background: #1565C0;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background: #37474F;
            }
            QPushButton {
                background: #1565C0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)

        # ── central ──
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── sidebar ──
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background: #263238;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Sidebar header
        header = QLabel("Component Gallery")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet("""
            color: white;
            background: #1A237E;
            padding: 16px;
        """)
        header.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(header)

        # Section labels and items
        self.list_widget = QListWidget()
        self._populate_sidebar()
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        sidebar_layout.addWidget(self.list_widget, 1)

        # Randomize button
        btn_container = QWidget()
        btn_container.setStyleSheet("background: #263238; padding: 8px;")
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(12, 8, 12, 12)

        self.randomize_btn = QPushButton("Randomize Mock Data")
        self.randomize_btn.clicked.connect(self._on_randomize)
        btn_layout.addWidget(self.randomize_btn)

        sidebar_layout.addWidget(btn_container)

        main_layout.addWidget(sidebar)

        # ── preview area ──
        self.preview_container = QWidget()
        self.preview_container.setStyleSheet("background: #ECEFF1;")
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(12, 12, 12, 12)

        # Component info label
        self.info_label = QLabel("Select a component from the sidebar")
        self.info_label.setFont(QFont("Segoe UI", 11))
        self.info_label.setStyleSheet("color: #546E7A; padding: 4px;")
        self.preview_layout.addWidget(self.info_label)

        # Preview widget holder
        self.current_widget = None
        self.widget_holder = QWidget()
        self.widget_holder.setStyleSheet("background: #ECEFF1;")
        self.preview_layout.addWidget(self.widget_holder, 1)

        main_layout.addWidget(self.preview_container, 1)

        # Select first item
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _populate_sidebar(self) -> None:
        """Fill the sidebar list with component entries grouped by family."""
        current_family = None
        family_labels = {
            "sqdp": "SQDP Graphs",
            "chart": "Charts",
            "table": "Tables",
            "control": "Controls & Selectors",
            "layout": "Layouts & Grids",
        }
        self._item_to_index = {}
        item_idx = 0

        for name, family, _ in COMPONENT_REGISTRY:
            if family != current_family:
                current_family = family
                # Section header (non-selectable)
                separator = QListWidgetItem(f"  {family_labels.get(family, family)}")
                separator.setFont(QFont("Segoe UI", 10, QFont.Bold))
                separator.setForeground(QColor("#90A4AE"))
                separator.setFlags(Qt.NoItemFlags)
                self.list_widget.addItem(separator)

            item = QListWidgetItem(f"    {name}")
            item.setFont(QFont("Segoe UI", 11))
            self.list_widget.addItem(item)
            self._item_to_index[self.list_widget.count() - 1] = item_idx
            item_idx += 1

    def _on_selection_changed(self, row: int) -> None:
        """Handle sidebar selection change — load the selected component."""
        if row < 0 or row not in self._item_to_index:
            return
        registry_idx = self._item_to_index[row]
        self._load_component(registry_idx)

    def _on_randomize(self) -> None:
        """Re-generate mock data for the currently selected component."""
        row = self.list_widget.currentRow()
        if row >= 0 and row in self._item_to_index:
            registry_idx = self._item_to_index[row]
            self._load_component(registry_idx)

    def _load_component(self, registry_idx: int) -> None:
        """Instantiate and display the component at the given registry index."""
        name, family, factory = COMPONENT_REGISTRY[registry_idx]

        # Remove old widget
        if self.current_widget is not None:
            self.preview_layout.removeWidget(self.current_widget)
            self.current_widget.deleteLater()
            self.current_widget = None

        # Remove old holder
        self.preview_layout.removeWidget(self.widget_holder)
        self.widget_holder.deleteLater()

        # Create new widget
        try:
            widget = factory()
            self.info_label.setText(f"{name}")
            self.info_label.setStyleSheet(
                "color: #1A237E; font-weight: bold; padding: 4px; font-size: 13px;"
            )
            
            if family == "control":
                # For control widgets (like Selection Bar), place at top (stretch=0)
                # and add an expanding graphic widget at the bottom (stretch=1)
                # so the selection bar stays compact and doesn't expand all over!
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(16)
                
                container_layout.addWidget(widget, 0)
                
                # Add sample expanding chart at the bottom
                bottom_chart = SqdpBarChartWidget(generate_bar_chart())
                container_layout.addWidget(bottom_chart, 1)
                
                # Connect update button to refresh the chart below!
                if hasattr(widget, "update_requested"):
                    widget.update_requested.connect(lambda fields: bottom_chart.set_data(generate_bar_chart()))
                
                self.current_widget = container
                self.preview_layout.addWidget(container, 1)
            else:
                self.current_widget = widget
                self.preview_layout.addWidget(widget, 1)
        except Exception as e:
            # Show error in info label
            error_label = QLabel(f"Error loading {name}:\n{e}")
            error_label.setStyleSheet("color: #F44336; padding: 20px; font-size: 12px;")
            error_label.setWordWrap(True)
            self.current_widget = error_label
            self.info_label.setText(f"{name} (ERROR)")
            self.info_label.setStyleSheet(
                "color: #F44336; font-weight: bold; padding: 4px; font-size: 13px;"
            )
            self.preview_layout.addWidget(error_label, 1)

        # Reset widget_holder for next time
        self.widget_holder = QWidget()


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gallery = ComponentGallery()
    gallery.show()
    sys.exit(app.exec_())
