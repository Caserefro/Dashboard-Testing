"""
components.selection_widget
===========================
Dynamic Selection Widget for interactive filtering and data selection.

Reference:
    Inspired by `draft Select widget.ui` (QFrame with QComboBox + QPushButton).

Features:
    1. **Programmatic / Code-Controlled Count**: In production usage, the number
       of field dropdowns is controlled purely by code via `num_fields` or
       `set_num_fields(n)`.
    2. **Optional Demo Count Selector**: If `show_count_selector=True` is passed,
       an interactive dropdown is displayed to let users test changing the number
       of dropdowns on the fly in demo applications.
    3. **Dynamic Field Dropdowns**: Automatically displays the requested number
       of QComboBoxes, each populated with the available fields.
    4. **Update Button**: One Update button at the end that gathers all selected
       values and emits `update_requested(list)`.
"""

from typing import List, Optional, Union
from PyQt5.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
    QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class DynamicSelectWidget(QFrame):
    """Dynamic selection bar with configurable number of field dropdowns.

    Args:
        available_fields: List of string options to show in each dropdown, OR a list of lists of strings
                          if each dropdown should have different options.
        num_fields: Initial number of field dropdowns to display (default 1).
        max_dropdowns: Maximum supported dropdowns (default 5).
        show_count_selector: If True, displays a UI dropdown to change `num_fields`
                             interactively (useful for demos/testing). Defaults to False.
        title: Optional title string displayed at the left of the widget (e.g. "SQDP Aspect:").
        field_labels: Optional list of custom labels for each dropdown (e.g. ["Start Period:", "End Period:"]).
        parent: Optional Qt parent widget.

    Signals:
        update_requested(list): Emitted when the Update button is clicked,
                                passing a list of selected field strings.
    """

    update_requested = pyqtSignal(list)

    def __init__(
        self,
        available_fields: Optional[Union[List[str], List[List[str]]]] = None,
        num_fields: int = 1,
        max_dropdowns: int = 5,
        show_count_selector: bool = False,
        title: Optional[str] = None,
        field_labels: Optional[List[str]] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.max_dropdowns = max_dropdowns
        self.num_fields = min(max(1, num_fields), max_dropdowns)
        self.show_count_selector = show_count_selector
        self.title = title
        self.field_labels = field_labels

        # Default dashboard fields if none provided
        if available_fields is None:
            self.available_fields = [
                "Safety — Ergonomics Assessment",
                "Safety — Chemical Exposure",
                "Quality — Scrap & Rework Rate",
                "Quality — Customer Defect Returns",
                "Delivery — On-Time Delivery (OTD)",
                "Delivery — Backlog & Late Orders",
                "Productivity — Overall Equipment Effectiveness (OEE)",
                "Productivity — Cycle Time Efficiency",
                "Pareto — Machine Breakdown Losses",
                "Pareto — Setup & Changeover Time",
            ]
        else:
            self.available_fields = available_fields

        # List of dynamically created QComboBoxes
        self.field_combos: List[QComboBox] = []

        self._setup_ui()
        self._apply_styles()
        
        # Apply initial visibility state
        self.set_num_fields(self.num_fields)

    def _setup_ui(self) -> None:
        """Initialize layout, optional count selector, dynamic container, and update button."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setMaximumHeight(85)

        # Main horizontal layout (like in draft Select widget.ui)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(12)
        self.main_layout.setAlignment(Qt.AlignVCenter)

        # ── 0. Optional Title / Header Label ──
        if self.title:
            title_lbl = QLabel(self.title)
            title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            title_lbl.setStyleSheet("color: #1E293B; padding-right: 6px;")
            self.main_layout.addWidget(title_lbl)

        # ── 1. Optional Count Selector (for Demo / Testing) ──
        self.count_container = QWidget()
        count_layout = QVBoxLayout(self.count_container)
        count_layout.setContentsMargins(0, 0, 0, 0)
        count_layout.setSpacing(4)
        count_layout.setAlignment(Qt.AlignVCenter)

        count_label = QLabel("Number of Fields:")
        count_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        count_label.setStyleSheet("color: #37474F;")
        count_layout.addWidget(count_label)

        self.count_combo = QComboBox()
        for i in range(1, self.max_dropdowns + 1):
            self.count_combo.addItem(f"{i} Field{'s' if i > 1 else ''}", i)
        self.count_combo.setCurrentIndex(self.num_fields - 1)
        self.count_combo.currentIndexChanged.connect(self._on_count_combo_changed)
        count_layout.addWidget(self.count_combo)

        self.main_layout.addWidget(self.count_container)

        # Separator line
        self.sep = QFrame()
        self.sep.setFrameShape(QFrame.VLine)
        self.sep.setFrameShadow(QFrame.Sunken)
        self.sep.setStyleSheet("color: #CFD8DC;")
        self.main_layout.addWidget(self.sep)

        # Hide count selector by default if not requested
        if not self.show_count_selector:
            self.count_container.hide()
            self.sep.hide()

        # ── 2. Dynamic Container for Field Dropdowns ──
        self.fields_container = QWidget()
        self.fields_layout = QHBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(10)
        self.fields_layout.setAlignment(Qt.AlignVCenter)
        self.main_layout.addWidget(self.fields_container, 1)  # Give stretch

        # Create all combo boxes up to max_dropdowns (initially hide unused ones)
        for i in range(self.max_dropdowns):
            combo_wrapper = QWidget()
            wrapper_layout = QVBoxLayout(combo_wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(4)
            wrapper_layout.setAlignment(Qt.AlignVCenter)

            if self.field_labels and i < len(self.field_labels):
                label_text = self.field_labels[i]
            else:
                label_text = f"Select Field #{i + 1}:"

            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
            lbl.setStyleSheet("color: #455A64;")
            wrapper_layout.addWidget(lbl)

            cb = QComboBox()
            if isinstance(self.available_fields, list) and len(self.available_fields) > 0 and isinstance(self.available_fields[0], list):
                # Different options per dropdown
                opts = self.available_fields[i] if i < len(self.available_fields) else self.available_fields[-1]
                cb.addItems(opts)
            else:
                # Same options across dropdowns
                cb.addItems(self.available_fields)
                if i < len(self.available_fields):
                    cb.setCurrentIndex(i)
            cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            wrapper_layout.addWidget(cb)

            self.field_combos.append(cb)
            self.fields_layout.addWidget(combo_wrapper)

        # ── 3. Update Button (like pushButton in draft Select widget.ui) ──
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()

        self.update_btn = QPushButton("Update Selection")
        self.update_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self._on_update_clicked)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addStretch()

        self.main_layout.addWidget(btn_container)

    def _apply_styles(self) -> None:
        """Apply modern, vibrant styling to the selection widget."""
        self.setStyleSheet("""
            DynamicSelectWidget {
                background-color: #FFFFFF;
                border: 1px solid #B0BEC5;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #F8FAFC;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 160px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
                background-color: #FFFFFF;
            }
            QComboBox:focus {
                border: 2px solid #2563EB;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: none;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #2563EB, stop:1 #1D4ED8);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #3B82F6, stop:1 #2563EB);
            }
            QPushButton:pressed {
                background: #1E40AF;
            }
        """)

    def set_num_fields(self, count: int) -> None:
        """Programmatically set the number of field dropdowns to display (code control)."""
        self.num_fields = min(max(1, count), self.max_dropdowns)
        
        # Sync combo if visible without re-triggering signal loop
        self.count_combo.blockSignals(True)
        self.count_combo.setCurrentIndex(self.num_fields - 1)
        self.count_combo.blockSignals(False)

        for i in range(self.max_dropdowns):
            wrapper = self.field_combos[i].parentWidget()
            if i < self.num_fields:
                wrapper.show()
            else:
                wrapper.hide()

    def _on_count_combo_changed(self, idx: int) -> None:
        """Handle user changing the demo count dropdown."""
        count = self.count_combo.itemData(idx)
        self.set_num_fields(count)

    def _on_update_clicked(self) -> None:
        """Gather selected fields, emit signal, and execute TODO action."""
        selected_fields = [
            self.field_combos[i].currentText() for i in range(self.num_fields)
        ]

        # Emit PyQt signal for external controllers
        self.update_requested.emit(selected_fields)

        # TODO: Implement concrete data updating logic here as needed
        print(f"[TODO] Update button clicked! Selected {self.num_fields} field(s):")
        for idx, field in enumerate(selected_fields, 1):
            print(f"  {idx}. {field}")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = DynamicSelectWidget(num_fields=3, show_count_selector=True)
    widget.resize(900, 100)
    widget.show()
    sys.exit(app.exec_())
