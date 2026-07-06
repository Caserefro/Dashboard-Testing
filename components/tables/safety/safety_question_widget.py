"""
components.tables.safety.safety_question_widget
===============================================
Interactive Safety Assessment Questionnaire Widget.

Purpose
-------
Renders a questionnaire card containing arbitrary safety prompts/questions
each followed by an interactive dropdown (QComboBox) of answer options.

As requested by the user, the prompt text and dropdown answer options are
completely decoupled and customizable—allowing any question text and any
list of answer choices (e.g. Motivation, Workload, Connected, Teamwork).

This widget performs **zero** business logic and relies completely on
:class:`models.table_models.SafetyQuestionnaireModel`.

Signals
-------
* ``answer_changed(int, str)``: Emitted when question at index changes text.
* ``answers_submitted(dict)``: Emitted when Submit button is clicked with all answers.
"""

from __future__ import annotations

from typing import Any, Optional, Dict, List
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


class SafetyAnswerWidget(QFrame):
    """Interactive safety assessment questionnaire widget.

    Parameters
    ----------
    model : SafetyQuestionnaireModel
        The questionnaire data model containing title and questions.
    already_filled : bool, optional
        If True, renders a completed message instead of interactive questions.
    parent : QWidget, optional
        Parent widget in the Qt object tree.
    """

    answer_changed = pyqtSignal(int, str)
    answers_submitted = pyqtSignal(dict)

    def __init__(
        self,
        model: Any,  # SafetyQuestionnaireModel
        already_filled: Optional[bool] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        if already_filled is not None:
            self.already_filled = already_filled
        else:
            self.already_filled = getattr(model, "already_filled", False)
        self._combos: List[QComboBox] = []

        self._setup_ui()
        self._apply_styles()
        self.set_data(model)

    def _setup_ui(self) -> None:
        """Initialize frame, header, questions container, and submit button without scrolling."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)

        # ── Header Title ──
        self.title_lbl = QLabel()
        self.title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("color: #0D47A1; background: #E3F2FD; padding: 8px; border-radius: 6px; border: 1px solid #90CAF9;")
        self.main_layout.addWidget(self.title_lbl)

        # ── Full Size Questions Container (No Scroll as requested) ──
        self.questions_container = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_container)
        self.questions_layout.setContentsMargins(0, 0, 0, 0)
        self.questions_layout.setSpacing(10)
        self.questions_layout.setAlignment(Qt.AlignTop)

        self.main_layout.addWidget(self.questions_container)

        # ── Submit Button ──
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        
        self.submit_btn = QPushButton("Submit Safety Assessment")
        self.submit_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.clicked.connect(self._on_submit_clicked)
        self.btn_layout.addWidget(self.submit_btn)
        self.btn_layout.addStretch()

        self.main_layout.addLayout(self.btn_layout)

    def _apply_styles(self) -> None:
        """Apply clean, professional dashboard styling."""
        self.setStyleSheet("""
            SafetyAnswerWidget {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #F8FAFC;
                color: #1E293B;
                border: 1px solid #94A3B8;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI';
                font-size: 13px;
                min-height: 24px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
                background-color: #FFFFFF;
            }
            QComboBox:focus {
                border: 2px solid #2563EB;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #1565C0, stop:1 #0D47A1);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #1E88E5, stop:1 #1565C0);
            }
            QPushButton:pressed {
                background: #0A387E;
            }
        """)

    def set_already_filled(self, filled: bool = True) -> None:
        """Dynamically switch between active questionnaire and completed message view."""
        self.already_filled = filled
        self.set_data(self._model)

    def set_data(self, model: Any) -> None:
        """Populate widget with questions or completed message from model."""
        self._model = model
        self.title_lbl.setText(model.title.upper() if model.title else "SAFETY ASSESSMENT")

        # Clear existing items
        while self.questions_layout.count():
            item = self.questions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._combos.clear()

        # ── Check Already Filled State ──
        if self.already_filled:
            self.submit_btn.setVisible(False)
            msg_card = QFrame()
            msg_card.setStyleSheet("QFrame { background: #ECFDF5; border: 1px solid #6EE7B7; border-radius: 8px; padding: 20px; }")
            msg_layout = QVBoxLayout(msg_card)
            msg_layout.setAlignment(Qt.AlignCenter)
            msg_layout.setSpacing(8)
            
            icon_lbl = QLabel("✅")
            icon_lbl.setFont(QFont("Segoe UI", 28))
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("border: none; background: transparent;")
            msg_layout.addWidget(icon_lbl)
            
            title_msg = QLabel("Assessment Already Submitted")
            title_msg.setFont(QFont("Segoe UI", 13, QFont.Bold))
            title_msg.setAlignment(Qt.AlignCenter)
            title_msg.setStyleSheet("color: #065F46; border: none; background: transparent;")
            msg_layout.addWidget(title_msg)
            
            sub_msg = QLabel(getattr(model, "completed_message", "Thank you! This safety assessment has already been filled and submitted for the current period."))
            sub_msg.setFont(QFont("Segoe UI", 10))
            sub_msg.setAlignment(Qt.AlignCenter)
            sub_msg.setWordWrap(True)
            sub_msg.setStyleSheet("color: #047857; border: none; background: transparent;")
            msg_layout.addWidget(sub_msg)
            
            self.questions_layout.addWidget(msg_card)
            return

        # ── Active Questionnaire View ──
        self.submit_btn.setVisible(True)
        for idx, q in enumerate(model.questions):
            card = QFrame()
            card.setStyleSheet("QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px; }")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(6)

            # Prompt label (above dropdown as requested)
            lbl = QLabel(q.prompt_text)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl.setStyleSheet("color: #1E293B; border: none; background: transparent;")
            lbl.setWordWrap(True)
            card_layout.addWidget(lbl)

            # Answer Dropdown
            cb = QComboBox()
            cb.addItems(q.options)
            if q.selected_option and q.selected_option in q.options:
                cb.setCurrentText(q.selected_option)
            
            cb.currentTextChanged.connect(lambda text, i=idx: self.answer_changed.emit(i, text))
            card_layout.addWidget(cb)

            self._combos.append(cb)
            self.questions_layout.addWidget(card)

    def get_answers(self) -> Dict[str, str]:
        """Return a dictionary mapping question prompts to currently selected answer strings."""
        result = {}
        for idx, q in enumerate(self._model.questions):
            if idx < len(self._combos):
                result[q.prompt_text] = self._combos[idx].currentText()
        return result

    def _on_submit_clicked(self) -> None:
        """Emit answers_submitted signal and transition to already_filled view."""
        answers = self.get_answers()
        self.answers_submitted.emit(answers)
        print("[SafetyAnswerWidget] Assessment Submitted:", answers)
        self.set_already_filled(True)


# Aliases for flexible dashboard naming
SafetyQuestionWidget = SafetyAnswerWidget
SafetyQuestionnaireWidget = SafetyAnswerWidget

