"""
test_sidebar.py — Collapsible Sidebar Demo & Graphic Widget Integration
=======================================================================

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
    python test_sidebar.py
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
from models.chart_models import BarChartModel, ProgressBarChartModel
from models.table_models import ParetoTableModel, ParetoLogTableModel, SafetyTableModel, SafetySummaryTableModel
from components.sqdp.sprint_1w_sqdp import Sprint1WSqdpWidget
from components.sqdp.sprint_2w_sqdp import Sprint2WSqdpWidget
from components.sqdp.daily_sqdp import DailySqdpWidget
from components.charts.sqdp_bar_chart import SqdpBarChartWidget
from components.charts.progress_bar_chart import ProgressBarChartWidget
from components.charts.burndown_chart import BurndownChartWidget
from components.charts.safety_bar_chart import SafetyBarChartWidget, StackedSafetyBarChart
from components.tables.pareto.pareto_table import ParetoTable
from components.tables.pareto.pareto_table_user import ParetoTableUser
from components.tables.pareto.pareto_table_admin import ParetoTableAdmin
from components.tables.safety.safety_table import SafetyTable
from components.tables.safety.safety_table_dashboard import SafetyTableDashboard
from components.tables.safety.safety_table_admin import SafetyTableAdmin
from components.tables.safety.safety_question_widget import SafetyAnswerWidget, SafetyQuestionWidget, SafetyQuestionnaireWidget
from components.tables.guide_table import TextGuideTable
from components.selection_widget import DynamicSelectWidget
from components.dashboard_grid import ScrollableDashboardGrid, GridItemConfig

# Mock data generators
from tools.component_gallery import (
    generate_sqdp_board,
    generate_bar_chart,
    generate_progress_chart,
    generate_pareto_table,
    generate_pareto_admin_table,
    generate_safety_table,
    generate_safety_summary_table,
    generate_safety_guide_table,
    generate_burndown_chart,
    generate_safety_bar_chart,
    generate_safety_questionnaire,
)


class SidebarDemoApp(QMainWindow):
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

        self.setWindowTitle("ProliverMaps — Collapsible Sidebar & Scrollable Dashboard Grids")

        # ── 1. Initialize Sidebar State (Start Collapsed) ──
        # menu_S = small icon-only menu (width 90)
        # menu_B = big expanded menu (width 230)
        self.menu_B.hide()
        self.menu_S.show()
        self.is_expanded = False

        # Connect Logo_S and Logo_L to toggle/expand the sidebar!
        self.Logo_S.setCursor(Qt.PointingHandCursor)
        self.Logo_L.setCursor(Qt.PointingHandCursor)
        self.Logo_S.mousePressEvent = lambda event: self.toggle_sidebar()
        self.Logo_L.mousePressEvent = lambda event: self.toggle_sidebar()

        # ── 2. Setup Menu Button Synchronisation ──
        # Map menu index -> (small_button, big_button, page_title)
        self.menu_items = [
            (self.Home_S,       self.pushButton_11, "Home — Executive Agile Dashboard (Where graphs exist)"),
            (self.Pedidos_S,    self.pushButton_12, "Data — Operations & Efficiency (Empty)"),
            (self.Clientes_S,   self.pushButton_13, "Users — Loss & Pareto Analysis (Empty)"),
            (self.Safety,       self.pushButton_15, "Safety — Physiological Assessment (Empty)"),
            (self.Cuotas_S,     self.pushButton_9,  "Calculations — Burndown & Safety (Empty)"),
            (self.Parametros_S, self.pushButton_14, "Settings — System & Controls (Empty)"),
            (self.Acerca_de_S,  self.pushButton_10, "Acerca de — No-Code Grid Architecture (Empty)"),
        ]

        for idx, (btn_s, btn_b, title) in enumerate(self.menu_items):
            btn_s.clicked.connect(lambda checked, i=idx: self.on_menu_clicked(i))
            btn_b.clicked.connect(lambda checked, i=idx: self.on_menu_clicked(i))

        # Connect close buttons
        self.Close_S.clicked.connect(self.close)
        self.pushButton_8.clicked.connect(self.close)

        # ── 3. Integrate Scrollable Dashboard Grids into UI Container ──
        # Widget_Area is the main content container in Dashboard_Testing.ui inside widget_5
        layout = QVBoxLayout(self.Widget_Area)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # ── PAGE 0: Home — Where ALL the graphs exist ──
        self.grid_home = ScrollableDashboardGrid(columns=2)
        # Row 0: Global Dashboard Filter
        self.grid_home.add_widget(DynamicSelectWidget(title="Global Dashboard Filter:", num_fields=3, show_count_selector=True), row=0, col=0, col_span=2, min_height=85)
        # Row 1: SQDP Board
        self.grid_home.add_widget(Sprint1WSqdpWidget(generate_sqdp_board("sprint_1w")), row=1, col=0, col_span=2, min_height=260)
        # Row 2 & 3: Burndown Chart (left) and SQDP Bar Chart + Aspect Selector (right)
        self.grid_home.add_widget(BurndownChartWidget(generate_burndown_chart()), row=2, col=0, row_span=2, min_height=465)
        self.grid_home.add_widget(SqdpBarChartWidget(generate_bar_chart()), row=2, col=1, min_height=380)
        self.grid_home.add_widget(
            DynamicSelectWidget(
                title="SQDP Aspect Filter:",
                field_labels=["Aspect:"],
                available_fields=["Safety (S)", "Quality (Q)", "Delivery (D)", "Productivity (P)"],
                num_fields=1,
                show_count_selector=False
            ),
            row=3, col=1, min_height=85
        )
        # Row 4 & 5: Progress Bar Chart + Period Selector (left) and Pareto Table (right)
        self.grid_home.add_widget(ProgressBarChartWidget(generate_progress_chart()), row=4, col=0, min_height=380)
        self.grid_home.add_widget(
            DynamicSelectWidget(
                title="Period Filter:",
                field_labels=["Start Period:", "End Period:"],
                available_fields=["Sprint 1 (Jan 1 - Jan 14)", "Sprint 2 (Jan 15 - Jan 28)", "Sprint 3 (Jan 29 - Feb 11)", "Sprint 4 (Feb 12 - Feb 25)", "Sprint 5 (Feb 26 - Mar 11)"],
                num_fields=2,
                show_count_selector=False
            ),
            row=5, col=0, min_height=85
        )
        self.grid_home.add_widget(ParetoTable(generate_pareto_table()), row=4, col=1, row_span=2, min_height=465)
        # Row 6: Revamped Safety Table Dashboard across bottom (Image 1 Summary Table)
        self.grid_home.add_widget(SafetyTableDashboard(generate_safety_summary_table()), row=6, col=0, col_span=2, min_height=140)
        # Row 7: Psychological Safety Metric Guide Table
        self.grid_home.add_widget(TextGuideTable(generate_safety_guide_table()), row=7, col=0, col_span=2, min_height=340)
        # Row 8: Safety Table Admin (Yellow Concern Log - Image 2 style, preserving old structure!)
        self.grid_home.add_widget(SafetyTableAdmin(generate_safety_table()), row=8, col=0, col_span=2, min_height=360)
        # Row 9: Pareto Table Admin (Yellow Loss Log with Inputs/Outputs!)
        self.grid_home.add_widget(ParetoTableAdmin(generate_pareto_admin_table()), row=9, col=0, col_span=2, min_height=360)

        # ── PAGE 1: Data — Loss & Pareto Analysis ──
        self.grid_data = ScrollableDashboardGrid(columns=2)
        self.grid_data.add_widget(ParetoTableAdmin(generate_pareto_admin_table()), row=0, col=0, col_span=2, min_height=360)
        self.grid_data.add_widget(ParetoTable(generate_pareto_table()), row=1, col=0, col_span=2, min_height=465)

        # ── PAGE 2: Users — Empty Screen ──
        self.grid_users = ScrollableDashboardGrid(columns=2)
        self.grid_users.add_widget(TextGuideTable(generate_safety_guide_table()), row=0, col=0, col_span=2, min_height=340)

        # ── PAGE 3: Safety — Complete Physiological Assessment View ──
        self.grid_safety = ScrollableDashboardGrid(columns=2)
        # Row 0: Psychological Safety Metric Guide Table
        self.grid_safety.add_widget(TextGuideTable(generate_safety_guide_table()), row=0, col=0, col_span=2, min_height=340)
        # Row 1: Revamped Safety Table Dashboard (Week 5 Summary Matrix)
        self.grid_safety.add_widget(SafetyTableDashboard(generate_safety_summary_table()), row=1, col=0, col_span=2, min_height=140)
        # Row 2: Interactive Answer Safety Questionnaire Widget (Active State)
        self.grid_safety.add_widget(SafetyAnswerWidget(generate_safety_questionnaire(already_filled=False)), row=2, col=0, col_span=2, min_height=350)
        # Row 3: Safety Answer Widget (Already Submitted State - Showing Completed Message)
        self.grid_safety.add_widget(SafetyAnswerWidget(generate_safety_questionnaire(already_filled=True)), row=3, col=0, col_span=2, min_height=180)
        # Row 4: Safety Table Admin (Yellow Concern Log - Image 2 style, preserving old structure!)
        self.grid_safety.add_widget(SafetyTableAdmin(generate_safety_table()), row=4, col=0, col_span=2, min_height=360)
        # Row 5: Safety Table Detailed Log (Old Standard Blue View)
        self.grid_safety.add_widget(SafetyTable(generate_safety_table()), row=5, col=0, col_span=2, min_height=360)

        # ── PAGE 4: Calculations — Empty Screen ──
        self.grid_calc = ScrollableDashboardGrid(columns=2)

        # ── PAGE 5: Settings — Empty Screen ──
        self.grid_settings = ScrollableDashboardGrid(columns=2)

        # ── PAGE 6: About — Empty Screen ──
        self.grid_about = ScrollableDashboardGrid(columns=2)

        # Add all grids to the content stack
        self.content_stack.addWidget(self.grid_home)     # Index 0: Home
        self.content_stack.addWidget(self.grid_data)     # Index 1: Data
        self.content_stack.addWidget(self.grid_users)    # Index 2: Users
        self.content_stack.addWidget(self.grid_safety)   # Index 3: Safety
        self.content_stack.addWidget(self.grid_calc)     # Index 4: Calculations
        self.content_stack.addWidget(self.grid_settings) # Index 5: Settings
        self.content_stack.addWidget(self.grid_about)    # Index 6: About

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


def main() -> None:
    app = QApplication(sys.argv)
    win = SidebarDemoApp()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR: Failed to launch Sidebar Demo.\nDetails: {e}")
        traceback.print_exc()
        sys.exit(1)
