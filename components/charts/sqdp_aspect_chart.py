from typing import Optional, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
)
from PyQt5.QtGui import QFont, QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSignal

from components.base import BaseGraphicContainer
from components.charts.sqdp_bar_chart import SqdpBarChartWidget
from components.charts.safety_bar_chart import SafetyBarChartWidget
from models.chart_models import BarChartModel
from tools.component_gallery import generate_bar_chart, generate_safety_bar_chart


class SqdpAspectChartWidget(BaseGraphicContainer):
    """
    Self-Contained SQDP Aspect Analysis & Chart Container.
    
    Features a sleek aspect selector bar right at the top:
      [S - Safety]  [Q - Quality]  [D - Delivery]  [P - Productivity]
    
    When 'S - Safety' is selected, it dynamically displays the SafetyBarChartWidget
    (Physiological breakdown: Motivation, Connected, Workload, Teamwork).
    When 'Q', 'D', or 'P' is selected, it displays their respective SqdpBarChartWidget metrics!
    """
    aspect_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(410)
        self._setup_ui()

    def _setup_ui(self) -> None:
        # BaseGraphicWidget renders card background. Layout adds controls with margins over card.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # ── Aspect Selector Header Bar ──
        row_header = QHBoxLayout()
        row_header.setSpacing(8)

        lbl_title = QLabel("SQDP Aspect Breakdown:", self)
        lbl_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_title.setStyleSheet("color: #FFFFFF;")
        row_header.addWidget(lbl_title)

        row_header.addStretch()

        self.buttons: Dict[str, QPushButton] = {}
        aspects = [
            ("S", "Safety", "#4CAF50"),
            ("Q", "Quality", "#FF9800"),
            ("D", "Delivery", "#2196F3"),
            ("P", "Productivity", "#00E676")
        ]

        for code, label, active_color in aspects:
            btn = QPushButton(f"{code} — {label}", self)
            btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setProperty("active_color", active_color)
            btn.clicked.connect(lambda checked, c=code: self.select_aspect(c))
            self.buttons[code] = btn
            row_header.addWidget(btn)

        layout.addLayout(row_header)

        # ── Stacked Chart Container ──
        self.chart_stack = QStackedWidget(self)

        # Index 0: S - Safety (SafetyBarChartWidget)
        self.widget_s = SafetyBarChartWidget(generate_safety_bar_chart())
        self.chart_stack.addWidget(self.widget_s)

        # Index 1: Q - Quality (SqdpBarChartWidget)
        quality_model = BarChartModel(
            title="Quality: First Time Yield & Scrap Rate",
            x_label="Weeks",
            categories=["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12"],
            values=[0.95, 0.98, 0.92, 0.88, 0.94, 0.97, 0.91, 0.89, 0.96, 0.99, 0.93, 0.90],
            target_threshold=0.93,
            y_max=1.0
        )
        self.widget_q = SqdpBarChartWidget(quality_model)
        self.chart_stack.addWidget(self.widget_q)

        # Index 2: D - Delivery (SqdpBarChartWidget)
        delivery_model = BarChartModel(
            title="Delivery: On-Time Order Fulfillment %",
            x_label="Weeks",
            categories=["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12"],
            values=[0.85, 0.92, 0.96, 0.91, 0.87, 0.94, 0.89, 0.93, 0.95, 0.88, 0.97, 0.92],
            target_threshold=0.90,
            y_max=1.0
        )
        self.widget_d = SqdpBarChartWidget(delivery_model)
        self.chart_stack.addWidget(self.widget_d)

        # Index 3: P - Productivity (SqdpBarChartWidget)
        self.widget_p = SqdpBarChartWidget(generate_bar_chart())
        self.chart_stack.addWidget(self.widget_p)

        layout.addWidget(self.chart_stack)

        # Default selection: P - Productivity (to match previous default slot) or S - Safety
        self.select_aspect("P")

    def select_aspect(self, code: str) -> None:
        """Switch chart stack and update button styles."""
        for c, btn in self.buttons.items():
            is_active = (c == code)
            btn.setChecked(is_active)
            active_clr = btn.property("active_color")
            if is_active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {active_clr};
                        color: #000000;
                        border: none;
                        border-radius: 5px;
                        padding: 5px 12px;
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #222222;
                        color: #AAAAAA;
                        border: 1px solid #383838;
                        border-radius: 5px;
                        padding: 5px 12px;
                    }
                    QPushButton:hover {
                        background-color: #2E2E2E;
                        color: #FFFFFF;
                    }
                """)

        mapping = {"S": 0, "Q": 1, "D": 2, "P": 3}
        if code in mapping:
            self.chart_stack.setCurrentIndex(mapping[code])
            self.aspect_changed.emit(code)

    def paint_content(self, painter: QPainter, rect) -> None:
        pass
