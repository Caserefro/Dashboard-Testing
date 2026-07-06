"""
apps.dashboard_app
==================
Unified WOR Dashboard application with role-based rendering.

Purpose
-------
Provides a single unified application for all daily management roles
(User, Focal, Admin) as specified in the project requirements. The role
or view mode determines which variants of the independent graphic
modules are rendered.

Views
-----
1. Dashboard View (Default): Standard dashboard overview rendering
   Sprint 1W SQDP, Efficiency Bar Chart, ESC Progress Chart, Pareto Table,
   and Safety Table.
2. User Entry View (Interactive): Renders Daily SQDP (31-cell),
   ParetoTableUser, and SafetyTableUser. Includes a Selection Widget
   with Dynamic Inputs for interactive data logging without embedding
   Qt controls inside the stateless graphic components.
3. Admin Review View: Renders Sprint 2W SQDP and ParetoTableAdmin (with
   colored heatmap emphasis on high-loss categories).
4. Focal Review View: Renders SafetyTableFocal with colored review status
   badges (Pending, Reviewed, Escalated).
"""

import sys
from datetime import date
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QHBoxLayout, QLabel, QComboBox, QStackedWidget, QFrame,
    QPushButton, QDoubleSpinBox, QLineEdit, QGroupBox, QFormLayout,
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

# ── Models ──
from models.sqdp_models import SqdpLetterModel, SqdpBoardModel
from models.chart_models import BarChartModel, ProgressBarChartModel
from models.table_models import ParetoTableModel, SafetyTableModel, SafetyFieldModel

# ── Components ──
from components.sqdp.sprint_1w_sqdp import Sprint1WSqdpWidget
from components.sqdp.sprint_2w_sqdp import Sprint2WSqdpWidget
from components.sqdp.daily_sqdp import DailySqdpWidget
from components.charts.sqdp_bar_chart import SqdpBarChartWidget
from components.charts.progress_bar_chart import ProgressBarChartWidget
from components.tables.pareto.pareto_table import ParetoTable
from components.tables.pareto.pareto_table_user import ParetoTableUser
from components.tables.pareto.pareto_table_admin import ParetoTableAdmin
from components.tables.safety.safety_table import SafetyTable
from components.tables.safety.safety_table_user import SafetyTableUser
from components.tables.safety.safety_table_focal import SafetyTableFocal

# ── Services & Repositories (Layered Architecture Composition Root) ──
from repositories.mock.mock_sqdp_repository import MockSqdpRepository
from repositories.mock.mock_chart_repository import MockChartRepository
from repositories.mock.mock_table_repository import MockTableRepository
from services.sqdp_service import SqdpService
from services.chart_service import ChartService
from services.table_service import TableService


class WORDashboardApp(QMainWindow):
    """Unified master dashboard application supporting all operational roles.

    Features a top toolbar with a view/role selector that dynamically
    switches the rendered graphic modules to match the user's workflow.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WOR Dashboard — Unified Visual Management")
        self.resize(1360, 800)
        self.setStyleSheet("QMainWindow { background: #ECEFF1; }")

        # Initialize Service-Repository Layer (Dependency Injection)
        self.sqdp_service = SqdpService(MockSqdpRepository())
        self.chart_service = ChartService(MockChartRepository())
        self.table_service = TableService(MockTableRepository())

        # Fetch initial data models via Services
        self.sqdp_1w_model = self.sqdp_service.get_processed_data(time_range="sprint_1w")
        self.sqdp_2w_model = self.sqdp_service.get_processed_data(time_range="sprint_2w")
        self.sqdp_daily_model = self.sqdp_service.get_processed_data(time_range="daily")
        self.bar_model = self.chart_service.get_processed_data(chart_type="bar")
        self.progress_model = self.chart_service.get_processed_data(chart_type="progress")
        self.pareto_model = self.table_service.get_processed_data(table_type="pareto")
        self.safety_model = self.table_service.get_processed_data(table_type="safety")

        # ── Central Widget & Layout ──
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        # ── Stacked View Area (create first so header can connect to it) ──
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._create_dashboard_view())
        self.stacked_widget.addWidget(self._create_user_entry_view())
        self.stacked_widget.addWidget(self._create_admin_view())
        self.stacked_widget.addWidget(self._create_focal_view())

        # ── Header Bar ──
        root.addWidget(self._create_header())
        root.addWidget(self.stacked_widget, 1)

        # ── Footer & Status Bar ──
        footer = QLabel("SOLID Visual Management Architecture • Pure Qt Custom Painting")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9, QFont.Bold))
        footer.setStyleSheet("color: #546E7A; padding: 2px;")
        root.addWidget(footer)

        today = date.today().strftime("%A, %B %d, %Y")
        self.statusBar().showMessage(f"  {today}  •  System Status: Online & Synchronised")
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #263238; color: #B0BEC5; font-size: 11px; }"
        )

    def _create_header(self) -> QWidget:
        """Create the top navigation header with role/view selector."""
        hdr = QWidget()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                         stop:0 #1A237E, stop:1 #1565C0);
            border-radius: 6px;
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(16, 0, 16, 0)

        team_lbl = QLabel("TeamName_DPT_202X")
        team_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        team_lbl.setStyleSheet("color: #BBDEFB;")
        lay.addWidget(team_lbl)

        lay.addStretch()

        title_lbl = QLabel("WOR Dashboard")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: white;")
        lay.addWidget(title_lbl)

        lay.addStretch()

        # Role / View Selector
        view_lbl = QLabel("Role Mode:")
        view_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        view_lbl.setStyleSheet("color: #BBDEFB;")
        lay.addWidget(view_lbl)

        self.view_selector = QComboBox()
        self.view_selector.addItems([
            "Dashboard View (Default)",
            "User Entry View (Interactive)",
            "Admin Review View (Heatmaps)",
            "Focal Review View (Status Badges)",
        ])
        self.view_selector.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.view_selector.setStyleSheet("""
            QComboBox {
                background: #FFFFFF;
                color: #1A237E;
                border: 1px solid #1565C0;
                border-radius: 4px;
                padding: 4px 12px;
                min-width: 220px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.view_selector.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)
        lay.addWidget(self.view_selector)

        return hdr

    # ── View 1: Dashboard View (Default) ──
    def _create_dashboard_view(self) -> QWidget:
        """Create the standard dashboard overview grid."""
        page = QWidget()
        grid = QGridLayout(page)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        sqdp = Sprint1WSqdpWidget(self.sqdp_1w_model)
        bar_chart = SqdpBarChartWidget(self.bar_model)
        progress_chart = ProgressBarChartWidget(self.progress_model)
        pareto = ParetoTable(self.pareto_model)

        grid.addWidget(sqdp,           0, 0)
        grid.addWidget(bar_chart,      0, 1)
        grid.addWidget(progress_chart, 1, 0)
        grid.addWidget(pareto,         1, 1)

        grid.setColumnStretch(0, 50)
        grid.setColumnStretch(1, 50)
        grid.setRowStretch(0, 50)
        grid.setRowStretch(1, 50)
        return page

    # ── View 2: User Entry View (Interactive) ──
    def _create_user_entry_view(self) -> QWidget:
        """Create the user submission view with dynamic selection input widget."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Daily SQDP (31-cell) + Pareto Table User
        left_widget = QWidget()
        left_grid = QVBoxLayout(left_widget)
        left_grid.setContentsMargins(0, 0, 0, 0)
        left_grid.setSpacing(8)

        daily_sqdp = DailySqdpWidget(self.sqdp_daily_model)
        self.pareto_user_table = ParetoTableUser(self.pareto_model, current_week_index=-1)
        
        left_grid.addWidget(daily_sqdp, 45)
        left_grid.addWidget(self.pareto_user_table, 55)
        layout.addWidget(left_widget, 65)

        # Right side: Safety Table User + Selection Input Widget
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.safety_user_table = SafetyTableUser(self.safety_model)
        right_layout.addWidget(self.safety_user_table, 60)

        # Dynamic Selection Widget for Table Entry
        input_group = QGroupBox("Dynamic Selection Input Widget (Pareto / Safety Logging)")
        input_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        input_group.setStyleSheet("""
            QGroupBox {
                background: #FFFFFF;
                border: 1px solid #CFD8DC;
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                color: #1A237E;
            }
        """)
        form_layout = QFormLayout(input_group)
        form_layout.setSpacing(10)

        self.target_table_combo = QComboBox()
        self.target_table_combo.addItems(["Pareto Loss Table", "Safety Metrics Table"])
        self.target_table_combo.currentIndexChanged.connect(self._on_target_table_changed)
        form_layout.addRow("Select Target:", self.target_table_combo)

        self.category_combo = QComboBox()
        self._populate_category_combo()
        form_layout.addRow("Category / Field:", self.category_combo)

        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setRange(0, 100)
        self.value_spinbox.setValue(5.0)
        form_layout.addRow("Loss Count / Value:", self.value_spinbox)

        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Enter optional comment or corrective action...")
        form_layout.addRow("Comment / Note:", self.comment_input)

        update_btn = QPushButton("Submit & Update Graph")
        update_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        update_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #388E3C; }
        """)
        update_btn.clicked.connect(self._on_submit_input)
        form_layout.addRow("", update_btn)

        right_layout.addWidget(input_group, 40)
        layout.addWidget(right_widget, 35)

        return page

    def _populate_category_combo(self) -> None:
        """Populate the category selector based on chosen target table."""
        self.category_combo.clear()
        if self.target_table_combo.currentIndex() == 0:
            # Pareto categories
            self.category_combo.addItems(self.pareto_model.categories)
        else:
            # Safety fields
            self.category_combo.addItems([f.field_name for f in self.safety_model.fields])

    def _on_target_table_changed(self, idx: int) -> None:
        """Update dynamic inputs when switching between Pareto and Safety targets."""
        self._populate_category_combo()
        if idx == 0:
            self.value_spinbox.setEnabled(True)
            self.value_spinbox.setPrefix("Count: ")
        else:
            self.value_spinbox.setEnabled(False)
            self.value_spinbox.setPrefix("N/A - ")

    def _on_submit_input(self) -> None:
        """Handle dynamic input submission by updating the DTO and repainting."""
        idx = self.target_table_combo.currentIndex()
        cat_idx = self.category_combo.currentIndex()
        if cat_idx < 0:
            return

        if idx == 0:
            # Update Pareto Table current week value
            val = self.value_spinbox.value()
            last_col_idx = len(self.pareto_model.columns) - 1
            self.pareto_model.values[cat_idx][last_col_idx] = val
            # Recalculate average
            row_vals = self.pareto_model.values[cat_idx]
            self.pareto_model.averages[cat_idx] = round(sum(row_vals) / len(row_vals), 1)
            self.table_service.save_data(self.pareto_model)
            self.pareto_user_table.set_data(self.pareto_model)
        else:
            # Update Safety Table comment
            comment = self.comment_input.text().strip()
            if comment:
                self.safety_model.fields[cat_idx].comment = comment
                self.safety_model.fields[cat_idx].field_value = "Updated"
                self.table_service.save_data(self.safety_model)
                self.safety_user_table.set_data(self.safety_model)
        
        self.comment_input.clear()

    # ── View 3: Admin Review View (Heatmaps) ──
    def _create_admin_view(self) -> QWidget:
        """Create the admin review view with Sprint 2W and Pareto heatmap."""
        page = QWidget()
        grid = QGridLayout(page)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        sqdp_2w = Sprint2WSqdpWidget(self.sqdp_2w_model)
        pareto_admin = ParetoTableAdmin(self.pareto_model)
        safety_table = SafetyTable(self.safety_model)

        grid.addWidget(sqdp_2w,      0, 0, 1, 2)
        grid.addWidget(pareto_admin, 1, 0)
        grid.addWidget(safety_table, 1, 1)

        grid.setRowStretch(0, 45)
        grid.setRowStretch(1, 55)
        grid.setColumnStretch(0, 55)
        grid.setColumnStretch(1, 45)
        return page

    # ── View 4: Focal Review View (Status Badges) ──
    def _create_focal_view(self) -> QWidget:
        """Create the focal review view with colored status review badges."""
        page = QWidget()
        grid = QGridLayout(page)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)

        # Set some sample status comments for focal review badges
        if len(self.safety_model.fields) >= 3:
            self.safety_model.fields[0].comment = "Reviewed"
            self.safety_model.fields[1].comment = "Pending"
            self.safety_model.fields[2].comment = "Escalated"

        safety_focal = SafetyTableFocal(self.safety_model)
        pareto_table = ParetoTable(self.pareto_model)

        grid.addWidget(safety_focal, 0, 0, 2, 1)
        grid.addWidget(pareto_table, 0, 1, 2, 1)

        grid.setColumnStretch(0, 55)
        grid.setColumnStretch(1, 45)
        return page


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WORDashboardApp()
    win.show()
    sys.exit(app.exec_())
