import sys
from datetime import date
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from typing import List, Dict, Any

from components.sqdp_widget import SQDPWidget
from components.bar_chart_widget import BarChartWidget
from components.esc_chart_widget import ESCChartWidget
from components.pareto_widget import ParetoWidget

# ══════════════════════════════════════════════════════════════
# DATA DEFINITIONS
# ══════════════════════════════════════════════════════════════

LETTERS_DATA: List[Dict[str, Any]] = [
    {
        "char": "S", "label": "Safety",
        "rows": 7, "cols": 4,
        "cells": [
            (0, 3), (0, 2), (0, 1),
            (1, 0), (2, 0),
            (3, 1), (3, 2), (3, 3),
            (4, 3), (5, 3),
            (6, 2), (6, 1), (6, 0),
        ],
        "status": [0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    },
    {
        "char": "Q", "label": "Quality",
        "rows": 7, "cols": 5,
        "cells": [
            (0, 1), (0, 2), (0, 3),
            (1, 4), (2, 4), (3, 4),
            (4, 3), (4, 2), (4, 1),
            (3, 0), (2, 0), (1, 0),
            (5, 4),
        ],
        "status": [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
    },
    {
        "char": "D", "label": "Delivery",
        "rows": 6, "cols": 5,
        "cells": [
            (0, 0), (0, 1), (0, 2), (0, 3),
            (1, 4), (2, 4), (3, 4),
            (4, 3), (4, 2), (4, 1), (4, 0),
            (3, 0), (2, 0), (1, 0),
        ],
        "status": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    {
        "char": "P", "label": "Productivity",
        "rows": 7, "cols": 4,
        "cells": [
            (3, 3), (2, 3), (1, 3),
            (0, 3), (0, 2), (0, 1), (0, 0),
            (1, 0), (2, 0), (3, 0),
            (4, 0), (5, 0), (6, 0),
        ],
        "status": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
]

BAR_CHART_DATA: Dict[str, Any] = {
    "title": "Productivity : How efficient are we being?",
    "x_label": "Weeks",
    "weeks": list(range(1, 14)),
    "values": [
        0.75, 0.82, 0.68, 0.91, 0.85,
        0.79, 0.88, 0.72, 0.95, 0.81,
        0.77, 0.90, 0.86,
    ],
    "green_thr": 0.8,
    "red_thr": 0.6,
}

_weeks_esc: List[int] = list(range(14, 39))
ESC_CHART_DATA: Dict[str, Any] = {
    "title": "ESC-A Verification Progress Inc. Year",
    "x_label": "Quarter",
    "weeks": _weeks_esc,
    "weekly": [
        120, 135, 110, 145, 160, 95, 155, 140, 125, 150,
        105, 140, 130, 165, 115, 138, 155, 120, 145, 100,
        150, 130, 115, 140, 125,
    ],
    "completed": [
        280, 290, 295, 305, 315, 318, 325, 332, 338, 345,
        350, 355, 358, 362, 365, 370, 374, 378, 382, 386,
        390, 394, 397, 400, 405,
    ],
    "total": [
        350, 358, 365, 372, 380, 387, 395, 402, 410, 418,
        425, 432, 440, 447, 455, 460, 465, 470, 475, 478,
        482, 485, 488, 492, 495,
    ],
    "y_max": 500,
}

PARETO_DATA: Dict[str, Any] = {
    "title": "Where Pareto",
    "weeks": [13, 14, 15, 16, 17, 18, 19],
    "categories": [
        "Support",
        "Mg availability",
        "Mg performance",
        "Task Planning",
        "Work Standards",
        "Training Needs",
        "Input Delays",
        "Input Quality",
    ],
    "values": [[0] * 7 for _ in range(8)],
    "averages": [0] * 8,
}

# ══════════════════════════════════════════════════════════════
# MAIN DASHBOARD APPLICATION
# ══════════════════════════════════════════════════════════════

class WORDashboard(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WOR Dashboard")
        self.resize(1280, 720)
        self.setStyleSheet("QMainWindow { background: #ECEFF1; }")

        # ── central ──
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 6, 10, 4)
        root.setSpacing(4)

        # ── header ──
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                         stop:0 #1A237E, stop:1 #1565C0);
            border-radius: 6px;
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 0, 16, 0)

        team_lbl = QLabel("TeamName_DPT_202X")
        team_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        team_lbl.setStyleSheet("color: #BBDEFB;")

        title_lbl = QLabel("WOR Dashboard")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: white;")
        title_lbl.setAlignment(Qt.AlignCenter)

        quarter_lbl = QLabel("Quarter 1")
        quarter_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        quarter_lbl.setStyleSheet("color: #BBDEFB;")
        quarter_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        hdr_lay.addWidget(team_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(quarter_lbl)

        root.addWidget(hdr)

        # ── grid of widgets ──
        grid = QGridLayout()
        grid.setSpacing(6)

        # Instantiate widgets passing the data
        sqdp = SQDPWidget(LETTERS_DATA)
        chart = BarChartWidget(BAR_CHART_DATA)
        esc_chart = ESCChartWidget(ESC_CHART_DATA)
        pareto = ParetoWidget(PARETO_DATA)

        grid.addWidget(sqdp,        0, 0)
        grid.addWidget(chart,       0, 1)
        grid.addWidget(esc_chart,   1, 0)
        grid.addWidget(pareto,      1, 1)

        grid.setColumnStretch(0, 55)
        grid.setColumnStretch(1, 45)
        grid.setRowStretch(0, 58)
        grid.setRowStretch(1, 42)

        root.addLayout(grid, 1)

        # ── footer ──
        footer = QLabel("Visual Management")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9, QFont.Bold))
        footer.setStyleSheet("color: #546E7A; padding: 2px;")
        root.addWidget(footer)

        # ── status bar ──
        total = sum(len(l["cells"]) for l in LETTERS_DATA)
        green = sum(sum(l["status"]) for l in LETTERS_DATA)
        pct = int(green / total * 100) if total else 0
        today = date.today().strftime("%A, %B %d, %Y")
        self.statusBar().showMessage(
            f"  {today}  •  Overall SQDP: {green}/{total} on target — {pct}%"
        )
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #263238; color: #B0BEC5; font-size: 11px; }"
        )

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        win = WORDashboard()
        win.show()
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR: Failed to run dashboard.\nDetails: {e}")
        traceback.print_exc()
        sys.exit(1)

