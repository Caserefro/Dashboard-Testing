"""
main.py — Dashboard Testing Main Application Entry Point
========================================================

Loads `Dashboard_Testing.ui` (from Qt Designer) and implements:
1. **Sidebar Collapse & Expand**: Toggles between the compact icon-only
   sidebar (`menu_S`, 90px) and the full expanded sidebar (`menu_B`, 230px)
   when clicking the menu button (`pushButton_15`).
2. **Menu State Synchronisation**: Keeps the checked states of buttons in
   `menu_S` and `menu_B` perfectly synchronized.
3. **SOLID Widget Integration**: Demonstrates how to embed our stateless
   graphic components (SQDP, Charts, Tables) directly into the Qt Designer
   UI container (`widget_3`) using a `QStackedWidget`.

Usage:
    python main.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QLabel, QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5 import uic

# Ensure compiled resources are imported so icons load cleanly
try:
    import resources_rc
except ImportError:
    pass

# ── Models & Components for Integration Demo ──
from models.sqdp_models import SqdpBoardModel
from models.chart_models import BarChartModel, ProgressBarChartModel, BurndownChartModel
from models.table_models import ParetoTableModel, ParetoLogTableModel, SafetyTableModel, SafetySummaryTableModel
from components.sqdp.sprint_1w_sqdp import Sprint1WSqdpWidget
from components.sqdp.sprint_2w_sqdp import Sprint2WSqdpWidget
from components.sqdp.daily_sqdp import DailySqdpWidget
from components.charts.sqdp_bar_chart import SqdpBarChartWidget
from components.charts.sqdp_aspect_chart import SqdpAspectChartWidget
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
from components.tables.guide_table import TextGuideTable
from components.selection_widget import DynamicSelectWidget
from components.period_filter_widget import PeriodFilterWidget, PeriodQueryModel
from components.dashboard_grid import ScrollableDashboardGrid, GridItemConfig
from components.json_viewer_widget import JsonContractViewerWidget

# Mock data generators
from tools.component_gallery import (
    generate_sqdp_board,
    generate_bar_chart,
    generate_progress_chart,
    generate_pareto_table,
    generate_pareto_admin_table,
    generate_pareto_category_table,
    generate_pareto_create_table,
    generate_safety_table,
    generate_safety_summary_table,
    generate_safety_guide_table,
    generate_burndown_chart,
    generate_safety_bar_chart,
    generate_safety_questionnaire,
)


class MainDashboardApp(QMainWindow):
    """Demonstration app combining the Qt Designer UI and SOLID graphic widgets.

    Features:
        - Collapsible sidebar: toggles between `menu_S` (small icons) and `menu_B` (full text).
        - SOLID Architecture: UI layout is loaded from `Dashboard_Testing.ui`, while custom
          graphic modules are dynamically inserted into `Widget_Area` via a `QStackedWidget`.
        - Scrollable Dashboard Grids: Each view in Widget_Area is a scrollable grid where
          multiple graphics (graphs, charts, tables, selectors) can be arranged declaratively.
    """

    def __init__(self) -> None:
        super().__init__()
        # Load the Qt Designer UI file
        ui_path = os.path.join(os.path.dirname(__file__), "Dashboard_Testing.ui")
        uic.loadUi(ui_path, self)

        self.setWindowTitle("Dashboard Testing — Collapsible Sidebar & Scrollable Dashboard Grids")

        # ── 1. Initialize Sidebar State (Start Collapsed) ──
        # menu_S = small icon-only menu (width 90)
        # menu_B = big expanded menu (width 230)
        self.menu_B.hide()
        self.menu_S.show()
        self.is_expanded = False

        # Connect Home_S_2 and Home_S_3 (top logo buttons) to toggle/expand the sidebar!
        self.Home_S_2.setCursor(Qt.PointingHandCursor)
        self.Home_S_3.setCursor(Qt.PointingHandCursor)
        self.Home_S_2.mousePressEvent = lambda event: self.toggle_sidebar()
        self.Home_S_3.mousePressEvent = lambda event: self.toggle_sidebar()

        # ── 2. Setup Menu Button Synchronisation ──
        # Map menu index -> (small_button, big_button, page_title)
        self.menu_items = [
            (self.Home_S,         self.Home_Ex,         "Home — Executive Agile Dashboard (Where graphs exist)"),
            (self.Safety_S,       self.Safety_Ex,       "Safety — Complete Physiological Assessment View"),
            (self.Pareto_S,       self.Pareto_Ex,       "Pareto — Loss Analysis & Audit Log"),
            (self.Data_S,         self.Data_Ex,         "Data — Operations & Efficiency (Empty)"),
            (self.Users_S,        self.Users_Ex,        "Users — User Management & Access (Empty)"),
            (self.Calculations_S, self.Calculations_Ex, "Calculations — Burndown & Safety Metrics (Empty)"),
            (self.Settings_S,     self.Settings_Ex,     "Settings — System & Controls (Empty)"),
            (self.About_S,        self.About_Ex,        "About — No-Code Grid Architecture (Empty)"),
        ]

        for idx, (btn_s, btn_b, title) in enumerate(self.menu_items):
            btn_s.clicked.connect(lambda checked, i=idx: self.on_menu_clicked(i))
            btn_b.clicked.connect(lambda checked, i=idx: self.on_menu_clicked(i))

        # Connect close buttons
        self.Close_S.clicked.connect(self.close)
        self.Close_Ex.clicked.connect(self.close)

        # ── 3. Integrate Scrollable Dashboard Grids into UI Container ──
        # Widget_Area is the main content container in Dashboard_Testing.ui inside widget_5
        layout = QVBoxLayout(self.Widget_Area)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # ── PAGE 0: Home — Where ALL the graphs exist ──
        self.grid_home = ScrollableDashboardGrid(columns=2)
        # Row 0: Global Timeframe / Period Filter
        self.filter_home = PeriodFilterWidget()
        self.filter_home.query_changed.connect(self._on_home_filter_changed)
        self.grid_home.add_widget(self.filter_home, row=0, col=0, col_span=2, min_height=100)
        # Row 1: SQDP Board
        self.sqdp_board_home = Sprint1WSqdpWidget(generate_sqdp_board("sprint_1w"))
        self.grid_home.add_widget(self.sqdp_board_home, row=1, col=0, col_span=2, min_height=210)
        # Row 2: Interactive SQDP Aspect Chart (Full Width across 2 columns)
        self.aspect_chart_home = SqdpAspectChartWidget()
        self.grid_home.add_widget(self.aspect_chart_home, row=2, col=0, col_span=2, min_height=420)
        # Row 3: Efficiency & Progress Combo Chart (Full Width across 2 columns)
        self.progress_home = ProgressBarChartWidget(generate_progress_chart())
        self.grid_home.add_widget(self.progress_home, row=3, col=0, col_span=2, min_height=380)
        # Row 4: Burndown Curve Chart (Full Width across 2 columns)
        self.burndown_home = BurndownChartWidget(generate_burndown_chart())
        self.grid_home.add_widget(self.burndown_home, row=4, col=0, col_span=2, min_height=380)
        # Row 5: Revamped Safety Table Dashboard across bottom (Summary Table)
        self.safety_summary_home = SafetyTableDashboard(generate_safety_summary_table())
        self.grid_home.add_widget(self.safety_summary_home, row=5, col=0, col_span=2, min_height=140)
        # Row 6: Pareto Table (Dashboard Loss Analysis)
        self.pareto_home = ParetoTable(generate_pareto_table())
        self.grid_home.add_widget(self.pareto_home, row=6, col=0, col_span=2, min_height=465)
        # Row 7: Pareto Table Admin (Yellow Loss Log with Date, Category, Comment!)
        self.pareto_admin_home = ParetoTableAdmin(generate_pareto_admin_table())
        self.grid_home.add_widget(self.pareto_admin_home, row=7, col=0, col_span=2, min_height=360)

        # ── PAGE 1: Data — Empty Screen ──
        self.grid_data = ScrollableDashboardGrid(columns=2)

        # ── PAGE 2: Users — Empty Screen ──
        self.grid_users = ScrollableDashboardGrid(columns=2)

        # ── PAGE 3: Safety — Complete Physiological Assessment View ──
        # ── PAGE 2: Safety — Assessment View ──
        self.grid_safety = ScrollableDashboardGrid(columns=2)

        # Row 0: Timeframe Selector
        self.grid_safety.add_widget(PeriodFilterWidget(), row=0, col=0, col_span=2, min_height=100)
        # Row 1: Safety Table Dashboard
        self.grid_safety.add_widget(SafetyTableDashboard(generate_safety_summary_table()), row=1, col=0, col_span=2,
                                    min_height=140)
        # Row 2: Questionnaire
        self.grid_safety.add_widget(SafetyAnswerWidget(generate_safety_questionnaire(already_filled=False)), row=2,
                                    col=0, col_span=2, min_height=350)
        # Row 3: Admin Concern Log
        self.grid_safety.add_widget(SafetyTableAdmin(generate_safety_table()), row=3, col=0, col_span=2, min_height=360)

        # ✅ Row 4: Safety Bar Chart (Full Width)
        self.grid_safety.add_widget(
            SafetyBarChartWidget(generate_safety_bar_chart()),
            row=4, col=0, col_span=2, min_height=380
        )

        # ── PAGE 4: Pareto — Loss Analysis & Audit Log ──
        self.grid_pareto = ScrollableDashboardGrid(columns=2)
        self.grid_pareto.add_widget(ParetoCategoryTable(generate_pareto_category_table()), row=0, col=0, col_span=2, min_height=250)
        self.grid_pareto.add_widget(ParetoTableAdmin(generate_pareto_admin_table()), row=1, col=0, col_span=2, min_height=300)
        self.grid_pareto.add_widget(ParetoTable(generate_pareto_table()), row=2, col=0, col_span=2, min_height=400)

        # ── PAGE 5: Calculations — CI Contract Viewer ──
        self.grid_calc = ScrollableDashboardGrid(columns=2)
        self.grid_calc.add_widget(JsonContractViewerWidget(), row=0, col=0, col_span=2, min_height=680)

        # ── PAGE 6: Settings — Empty Screen ──
        self.grid_settings = ScrollableDashboardGrid(columns=2)

        # ── PAGE 7: About — Empty Screen ──
        self.grid_about = ScrollableDashboardGrid(columns=2)

        # Add all grids to the content stack in the updated menu order
        self.content_stack.addWidget(self.grid_home)     # Index 0: Home
        self.content_stack.addWidget(self.grid_safety)   # Index 1: Safety
        self.content_stack.addWidget(self.grid_pareto)   # Index 2: Pareto
        self.content_stack.addWidget(self.grid_data)     # Index 3: Data
        self.content_stack.addWidget(self.grid_users)    # Index 4: Users
        self.content_stack.addWidget(self.grid_calc)     # Index 5: Calculations
        self.content_stack.addWidget(self.grid_settings) # Index 6: Settings
        self.content_stack.addWidget(self.grid_about)    # Index 7: About

        # Select the first item by default
        self.on_menu_clicked(0)

    def toggle_sidebar(self) -> None:
        """Toggle between collapsed (menu_S) and expanded (menu_B) sidebar."""
        if self.is_expanded:
            # Collapse sidebar
            self.menu_B.hide()
            self.menu_S.show()
            self.is_expanded = False
        else:
            # Expand sidebar
            self.menu_S.hide()
            self.menu_B.show()
            self.is_expanded = True

    def on_menu_clicked(self, idx: int) -> None:
        """Handle menu navigation, sync checked button states, and update stack."""
        for i, (btn_s, btn_b, title) in enumerate(self.menu_items):
            is_active = (i == idx)
            btn_s.setChecked(is_active)
            btn_b.setChecked(is_active)
            if is_active:
                # Update top header title label in Dashboard_Testing.ui
                self.Title_Card.setText(f"<html><head/><body><p><span style='font-size:14pt;'>{title}</span></p></body></html>")
                # Switch displayed graphic widget
                self.content_stack.setCurrentIndex(i)

    def _on_home_filter_changed(self, query: PeriodQueryModel) -> None:
        """Reactive Slot: dynamically refreshes Home tab widgets when time or team query changes."""
        print(f"[UI REACTIVE LOOP] Updating Home Dashboard -> Granularity: {query.granularity} | Window: {query.period_window} | Scope: {query.team_selection}")
        
        # 1. Dynamically adapt Burndown curve X-axis and baseline based on selected time window!
        if query.granularity == "Fiscal Weeks":
            new_burndown = BurndownChartModel(
                title=f"Burndown Curve ({query.period_window}) — {query.team_selection}",
                x_label="Quarter Progress (Fiscal Weeks)",
                y_label="Remaining Backlog Points",
                x_categories=["W1", "W3", "W5", "W7", "W9", "W11", "W13"],
                x_smooth=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                line_master=[500.0, 400.0, 300.0, 200.0, 100.0, 0.0],
                x_live=[0.0, 0.2, 0.4],
                y_live=[500.0, 420.0, 310.0],
                x_future=[0.4, 0.6, 0.8, 1.0],
                line_slip=[310.0, 220.0, 130.0, 40.0],
                line_catchup=[310.0, 200.0, 100.0, 0.0],
                y_max=550.0,
                deadline_delta=40.0
            )
        else:
            new_burndown = BurndownChartModel(
                title=f"Burndown Curve ({query.period_window}) — {query.team_selection}",
                x_label="Sprint Burndown Unavailable",
                y_label="",
                x_categories=[],
                x_smooth=[],
                line_master=[],
                x_live=[],
                y_live=[],
                x_future=[],
                line_slip=[],
                line_catchup=[],
                y_max=100.0,
                deadline_delta=0.0
            )
        self.burndown_home.set_data(new_burndown)
        
        # 2. Update Progress Chart Title & Targets to match exact room code/team!
        new_progress = ProgressBarChartModel(
            title=f"Efficiency & Progress Ratio — {query.team_selection} ({query.fiscal_year})",
            x_label="Sectors / Work Cells",
            categories=["Cell A", "Cell B", "Cell C", "Cell D", "Cell E", "Cell F"],
            bar_values=[0.92, 0.88, 0.95, 0.84, 0.91, 0.96],
            line_completed=[0.90, 0.85, 0.94, 0.82, 0.89, 0.95],
            line_total=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            y_max=1.0
        )
        self.progress_home.set_data(new_progress)


# Backwards compatibility alias
SidebarDemoApp = MainDashboardApp


def main() -> None:
    app = QApplication(sys.argv)
    win = MainDashboardApp()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR: Failed to launch Main Dashboard Application.\nDetails: {e}")
        traceback.print_exc()
        sys.exit(1)

