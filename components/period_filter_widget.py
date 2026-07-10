from dataclasses import dataclass
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit
)
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtCore import Qt, pyqtSignal

from components.base import BaseGraphicContainer
from components.theme import HEADER_CLR, SUBTEXT
from models.query_models import PeriodQueryModel


class PeriodFilterWidget(BaseGraphicContainer):
    """
    Domain-Specific Period, Timeframe & Team Scope Query Widget (100% Parameterized & Reusable).
    
    Replaces generic multi-field selectors when filtering dashboard data by time & team scope.
    Features:
      1. Cascading Time Dropdowns (`Granularity` -> `Quarter/Month Window`).
      2. Team / Scope Selector (`Cell 4`, `Machining`, `Entire Plant`, etc.).
      3. Among Us / Lobby Style Room Code Joiner (`Join Room Code: [XR9-8B2] [+ Join]`).
    
    Emits `query_changed(PeriodQueryModel)` when the user clicks 'Update Dashboard'.
    """
    query_changed = pyqtSignal(PeriodQueryModel)

    def __init__(
        self,
        granularities: Optional[List[str]] = None,
        options_map: Optional[Dict[str, List[str]]] = None,
        fiscal_years: Optional[List[str]] = None,
        teams: Optional[List[str]] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setMinimumHeight(95)
        self.setMaximumHeight(125)

        # Default granularities
        self.granularities = granularities if granularities is not None else ["Fiscal Weeks", "Days"]

        # Default cascading options map with all 12 calendar months & FW quarters without 'Last 2 weeks'
        if options_map is not None:
            self.options_map = options_map
        else:
            self.options_map = {
                "Fiscal Weeks": [
                    "Q1 (Weeks 1–13)",
                    "Q2 (Weeks 14–26)",
                    "Q3 (Weeks 27–39)",
                    "Q4 (Weeks 40–52)"
                ],
                "Days": [
                    "January (Days 1–31)",
                    "February (Days 1–28)",
                    "March (Days 1–31)",
                    "April (Days 1–30)",
                    "May (Days 1–31)",
                    "June (Days 1–30)",
                    "July (Days 1–31)",
                    "August (Days 1–31)",
                    "September (Days 1–30)",
                    "October (Days 1–31)",
                    "November (Days 1–30)",
                    "December (Days 1–31)"
                ]
            }

        # Default fiscal years
        self.fiscal_years = fiscal_years if fiscal_years is not None else ["FY 2026", "FY 2025", "FY 2024"]

        # Default teams
        self.teams = teams if teams is not None else [
            "Cell 4 (Assembly)",
            "Cell 1 (Machining)",
            "Maintenance & Facilities",
            "Quality Assurance",
            "Entire Plant / All Teams"
        ]

        self._setup_ui()

    def _setup_ui(self) -> None:
        # BaseGraphicWidget paints card background. We add controls over it with compact margins so all columns fit.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        # ── Left Title ──
        title_label = QLabel("Dashboard\nFilter:", self)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {HEADER_CLR.name()};")
        layout.addWidget(title_label)

        # ── Dropdown 1: Granularity ──
        box_granularity = QVBoxLayout()
        box_granularity.setSpacing(4)
        lbl_gran = QLabel("Granularity:", self)
        lbl_gran.setFont(QFont("Segoe UI", 8))
        lbl_gran.setStyleSheet("color: #AAAAAA;")
        box_granularity.addWidget(lbl_gran)

        self.combo_granularity = QComboBox(self)
        self.combo_granularity.addItems(self.granularities)
        self.combo_granularity.setFont(QFont("Segoe UI", 9))
        self.combo_granularity.setMinimumWidth(115)
        self.combo_granularity.setStyleSheet(self._combo_stylesheet())
        self.combo_granularity.currentIndexChanged.connect(self._on_granularity_changed)
        box_granularity.addWidget(self.combo_granularity)
        layout.addLayout(box_granularity)

        # ── Dropdown 2: Time Window (Cascading from options_map) ──
        box_window = QVBoxLayout()
        box_window.setSpacing(4)
        lbl_win = QLabel("Quarter / Month Window:", self)
        lbl_win.setFont(QFont("Segoe UI", 8))
        lbl_win.setStyleSheet("color: #AAAAAA;")
        box_window.addWidget(lbl_win)

        self.combo_window = QComboBox(self)
        self.combo_window.setFont(QFont("Segoe UI", 9))
        self.combo_window.setMinimumWidth(170)
        self.combo_window.setStyleSheet(self._combo_stylesheet())
        box_window.addWidget(self.combo_window)
        layout.addLayout(box_window)

        # ── Dropdown 3: Fiscal Year ──
        box_year = QVBoxLayout()
        box_year.setSpacing(4)
        lbl_yr = QLabel("Fiscal Year:", self)
        lbl_yr.setFont(QFont("Segoe UI", 8))
        lbl_yr.setStyleSheet("color: #AAAAAA;")
        box_year.addWidget(lbl_yr)

        self.combo_year = QComboBox(self)
        self.combo_year.addItems(self.fiscal_years)
        self.combo_year.setFont(QFont("Segoe UI", 9))
        self.combo_year.setMinimumWidth(90)
        self.combo_year.setStyleSheet(self._combo_stylesheet())
        box_year.addWidget(self.combo_year)
        layout.addLayout(box_year)

        # ── Dropdown 4: Team / Scope ──
        box_team = QVBoxLayout()
        box_team.setSpacing(4)
        lbl_team = QLabel("Team / Scope:", self)
        lbl_team.setFont(QFont("Segoe UI", 8))
        lbl_team.setStyleSheet("color: #AAAAAA;")
        box_team.addWidget(lbl_team)

        self.combo_team = QComboBox(self)
        self.combo_team.addItems(self.teams)
        self.combo_team.setFont(QFont("Segoe UI", 9))
        self.combo_team.setMinimumWidth(150)
        self.combo_team.setStyleSheet(self._combo_stylesheet())
        box_team.addWidget(self.combo_team)
        layout.addLayout(box_team)

        # ── Among Us / Jackbox Room Code Joiner ──
        box_room = QVBoxLayout()
        box_room.setSpacing(4)
        lbl_room = QLabel("Join Room Code:", self)
        lbl_room.setFont(QFont("Segoe UI", 8))
        lbl_room.setStyleSheet("color: #00E676; font-weight: bold;")
        box_room.addWidget(lbl_room)

        row_room_input = QHBoxLayout()
        row_room_input.setSpacing(6)

        self.input_room_code = QLineEdit(self)
        self.input_room_code.setPlaceholderText("CODE (e.g. XR9-8B)")
        self.input_room_code.setMaxLength(8)
        self.input_room_code.setFont(QFont("Consolas", 9, QFont.Bold))
        self.input_room_code.setMinimumWidth(125)
        self.input_room_code.setStyleSheet("""
            QLineEdit {
                background-color: #1E293B;
                color: #00E676;
                border: 1px solid #00E676;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 2px solid #00FF88;
                background-color: #0F172A;
            }
        """)
        self.input_room_code.returnPressed.connect(self._on_join_room_clicked)
        row_room_input.addWidget(self.input_room_code)

        self.btn_join_room = QPushButton("+ Join", self)
        self.btn_join_room.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.btn_join_room.setCursor(Qt.PointingHandCursor)
        self.btn_join_room.setStyleSheet("""
            QPushButton {
                background-color: #00C853;
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00E676;
            }
            QPushButton:pressed {
                background-color: #009624;
            }
        """)
        self.btn_join_room.clicked.connect(self._on_join_room_clicked)
        row_room_input.addWidget(self.btn_join_room)

        box_room.addLayout(row_room_input)
        layout.addLayout(box_room)

        layout.addStretch()

        # ── Action Button: Update Dashboard ──
        self.btn_update = QPushButton("Update Dashboard", self)
        self.btn_update.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setMinimumSize(135, 36)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #1F69FF;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #3B7DFF;
            }
            QPushButton:pressed {
                background-color: #1550CC;
            }
        """)
        self.btn_update.clicked.connect(self._emit_query)
        layout.addWidget(self.btn_update, alignment=Qt.AlignBottom)

        # Connect dropdown changes for immediate real-time reactivity (granularity handled by _on_granularity_changed)
        self.combo_window.currentIndexChanged.connect(lambda _: self._emit_query())
        self.combo_year.currentIndexChanged.connect(lambda _: self._emit_query())
        self.combo_team.currentIndexChanged.connect(lambda _: self._emit_query())

        # Populate combo_window initially (which calls _emit_query cleanly once)
        self._on_granularity_changed(0)

    def _combo_stylesheet(self) -> str:
        return """
            QComboBox {
                background-color: #252525;
                color: #E0E0E0;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QComboBox:hover {
                border-color: #1F69FF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: none;
            }
        """

    def _on_granularity_changed(self, idx: int) -> None:
        """Cascading logic: populate time window dropdown based on Granularity selection from options_map."""
        granularity = self.combo_granularity.currentText()
        self.combo_window.blockSignals(True)
        self.combo_window.clear()
        items = self.options_map.get(granularity, [])
        if items:
            self.combo_window.addItems(items)
        self.combo_window.blockSignals(False)
        self._emit_query()

    def _on_join_room_clicked(self) -> None:
        """Among Us / Lobby style room code joining logic."""
        code = self.input_room_code.text().strip().upper()
        if not code:
            return
        
        room_label = f"Lobby: {code}"
        
        # Check if already in dropdown to avoid duplicates
        existing_idx = self.combo_team.findText(room_label)
        if existing_idx >= 0:
            self.combo_team.setCurrentIndex(existing_idx)
        else:
            self.combo_team.addItem(room_label)
            self.combo_team.setCurrentIndex(self.combo_team.count() - 1)
        
        self.input_room_code.clear()
        self.input_room_code.setPlaceholderText(f"Joined {code}!")

    def _emit_query(self) -> None:
        """Build and emit the PeriodQueryModel."""
        if not self.combo_window.currentText() or not self.combo_granularity.currentText():
            return
        team_text = self.combo_team.currentText()
        room_code = None
        if team_text.startswith("Lobby: "):
            room_code = team_text.replace("Lobby: ", "").strip()

        query = PeriodQueryModel(
            granularity=self.combo_granularity.currentText(),
            period_window=self.combo_window.currentText(),
            fiscal_year=self.combo_year.currentText(),
            team_selection=team_text,
            room_code=room_code
        )
        self.query_changed.emit(query)

    def get_current_query(self) -> PeriodQueryModel:
        team_text = self.combo_team.currentText()
        room_code = None
        if team_text.startswith("Lobby: "):
            room_code = team_text.replace("Lobby: ", "").strip()

        return PeriodQueryModel(
            granularity=self.combo_granularity.currentText(),
            period_window=self.combo_window.currentText(),
            fiscal_year=self.combo_year.currentText(),
            team_selection=team_text,
            room_code=room_code
        )

    def paint_content(self, painter: QPainter, rect) -> None:
        # Layout handles all child widget rendering over the card
        pass
