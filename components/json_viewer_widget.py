import os
import json
from typing import Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

class JsonContractViewerWidget(QWidget):
    """
    Plain text widget displaying config/ui_graph_contracts.json directly on the dashboard tab.
    Allows easy demonstration of the CI schema during presentations and design reviews.
    """
    def __init__(self, file_path: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, "config", "ui_graph_contracts.json")
        self.file_path = file_path

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header Title
        title_label = QLabel("Immutable CI Gate Schema — ui_graph_contracts.json", self)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #FFFFFF; padding: 4px 0px;")
        layout.addWidget(title_label)

        # Subtitle explanation
        subtitle_label = QLabel(
            "This static contract is validated offline exactly once during CI before 'docker build'.\n"
            "All widgets below/across tabs render directly from valid database snapshots without runtime overhead.",
            self
        )
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #AAAAAA; padding-bottom: 4px;")
        layout.addWidget(subtitle_label)

        # Plain Text Viewer
        self.text_editor = QPlainTextEdit(self)
        self.text_editor.setReadOnly(True)
        self.text_editor.setFont(QFont("Consolas", 10))
        self.text_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1A1A1A;
                color: #A5D6FF;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px;
                selection-background-color: #264F78;
            }
        """)

        # Load file content
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_editor.setPlainText(content)
            except Exception as e:
                self.text_editor.setPlainText(f"Error loading {self.file_path}:\n{e}")
        else:
            self.text_editor.setPlainText(f"File not found: {self.file_path}")

        layout.addWidget(self.text_editor)
