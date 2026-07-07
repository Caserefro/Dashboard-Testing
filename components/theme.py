"""Centralized Color Configuration Hub for ProliverMaps Dashboard.

This module defines all visual design tokens, color palettes, and rendering helpers
used across every graphic component family (SQDP grids, charts, tables, questionnaires).
Having all colors centralized here makes styling adjustments and theme customizations
effortless and consistent across the entire codebase.
"""

from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF

# ══════════════════════════════════════════════════════════════
# 1. CORE & CARD PALETTE (Backgrounds, borders, shadows, text)
# ══════════════════════════════════════════════════════════════
BG_WHITE     = QColor("#FFFFFF")
BG_CARD      = QColor("#FFFFFF")
HEADER_CLR   = QColor("#212121")  # Main headings and titles
SUBTEXT      = QColor("#757575")  # Secondary labels and subtitles
TEXT_WHITE   = QColor("#FFFFFF")  # Text on dark/vibrant backgrounds
GRID_LINE    = QColor("#E0E0E0")  # Axis lines and card borders
CELL_BORDER  = QColor("#333333")  # SQDP cell borders

# ══════════════════════════════════════════════════════════════
# 2. SQDP LETTER GRIDS PALETTE (S, Q, D, P status cells)
# ══════════════════════════════════════════════════════════════
GREEN        = QColor("#4CAF50")  # Target met / Good status
GREEN_LIGHT  = QColor("#66BB6A")  # Gradient top for green cells
RED          = QColor("#F44336")  # Target missed / Attention needed
RED_LIGHT    = QColor("#EF5350")  # Gradient top for red cells
ORANGE       = QColor("#FF9800")  # Warning / Caution status
NAVY         = QColor("#1A237E")  # Deep primary branding

# ══════════════════════════════════════════════════════════════
# 3. CHARTS PALETTE (Safety bar, Progress combo, Burndown)
# ══════════════════════════════════════════════════════════════
# Progress Bar & Combo Charts
PROGRESS_BAR_CLR     = QColor("#1A237E")  # Vertical periodic bars (Navy)
PROGRESS_ACTUAL_LINE = QColor("#212121")  # Cumulative actual progress line
PROGRESS_TARGET_LINE = QColor("#1976D2")  # Cumulative target line (Accent Blue)
ORANGE_BAR           = QColor("#F57C00")  # Secondary/warning bars
ACCENT_BLUE          = QColor("#1976D2")  # General blue highlights

# Safety Stacked & Side-by-Side Bar Charts
SAFETY_MOTIVATION_CLR = QColor("#757575")  # Motivation metric (Grey)
SAFETY_CONNECTED_CLR  = QColor("#1565C0")  # Connection metric (Dark Blue)
SAFETY_WORKLOAD_CLR   = QColor("#F57C00")  # Workload metric (Amber/Orange)
SAFETY_TEAMWORK_CLR   = QColor("#29B6F6")  # Teamwork metric (Light Blue/Cyan)
SAFETY_AXIS_CLR       = QColor("#1E293B")  # Chart axis and bar outline

# Burndown Chart Lines
BURNDOWN_MASTER_CLR  = QColor("#8D99AE")  # Master/Baseline curve (Grey)
BURNDOWN_LIVE_CLR    = QColor("#D90429")  # Live tracking curve (Red)
BURNDOWN_SLIP_CLR    = QColor("#F4A261")  # Slipped target curve (Orange)
BURNDOWN_CATCHUP_CLR = QColor("#1D3557")  # Catch-up trajectory (Dark Blue)
BURNDOWN_GRID_CLR    = QColor("#E0E0E0")  # Background reference grid

# ══════════════════════════════════════════════════════════════
# 4. STANDARD BLUE TABLES PALETTE (Pareto & Detailed Logs)
# ══════════════════════════════════════════════════════════════
TBL_HDR_BG       = QColor("#1565C0")  # Primary blue table header
TBL_HDR_BORDER   = QColor("#0D47A1")  # Darker blue border for headers
TBL_ALT_ROW      = QColor("#F5F5F5")  # Alternating row background
TBL_TITLE_BG     = QColor("#E3F2FD")  # Guide/section title banner background
TBL_TITLE_BORDER = QColor("#0D47A1")  # Guide/section title border

# ══════════════════════════════════════════════════════════════
# 5. YELLOW / GOLD ADMIN TABLES PALETTE (Pareto & Safety Admin)
# ══════════════════════════════════════════════════════════════
ADMIN_GOLD_HDR_BG = QColor("#FFF59D")  # Yellow theme header background
ADMIN_GOLD_BORDER = QColor("#FBC02D")  # Yellow theme header border
ADMIN_GOLD_TEXT   = QColor("#5D4037")  # Warm brown header text
ADMIN_ROW_EVEN    = QColor("#FFFFFF")  # Even row white background
ADMIN_ROW_ODD     = QColor("#FFFDE7")  # Odd row soft yellow tint

# Badge Color Palette for Categories (cycled based on category name)
ADMIN_BADGE_PALETTE = [
    QColor("#E53935"),  # Red
    QColor("#FB8C00"),  # Orange
    QColor("#1E88E5"),  # Blue
    QColor("#43A047"),  # Green
    QColor("#8E24AA"),  # Purple
    QColor("#00897B"),  # Teal
]

# ══════════════════════════════════════════════════════════════
# 6. SAFETY DASHBOARD SUMMARY MATRIX PALETTE (Week Summary)
# ══════════════════════════════════════════════════════════════
SUMMARY_HDR_BG     = QColor("#D9EAFD")  # Soft blue header banner
SUMMARY_HDR_TEXT   = QColor("#0D47A1")  # Dark blue header text
SUMMARY_TOTAL_BG   = QColor("#FF9800")  # Orange highlight for Total column
SUMMARY_TOTAL_TEXT = QColor("#FFFFFF")  # White text on Total column
SUMMARY_SCORE_GREEN  = QColor("#A5D6A7")  # Good score badge background
SUMMARY_SCORE_YELLOW = QColor("#FFF59D")  # Moderate score badge background
SUMMARY_SCORE_RED    = QColor("#EF9A9A")  # Critical score badge background

# ══════════════════════════════════════════════════════════════
# 7. SAFETY QUESTIONNAIRE PALETTE (Interactive & Submitted)
# ══════════════════════════════════════════════════════════════
QUESTION_TITLE_BG     = QColor("#E3F2FD")  # Questionnaire banner background
QUESTION_TITLE_TEXT   = QColor("#1565C0")  # Questionnaire banner text
QUESTION_INPUT_BG     = QColor("#FFFFFF")  # Dropdown box background
QUESTION_INPUT_BORDER = QColor("#B0BEC5")  # Dropdown border
QUESTION_BTN_BG       = QColor("#1565C0")  # Submit button background
QUESTION_BTN_TEXT     = QColor("#FFFFFF")  # Submit button text
QUESTION_SUCCESS_BG   = QColor("#E8F5E9")  # Submitted state green banner
QUESTION_SUCCESS_TEXT = QColor("#1B5E20")  # Submitted state green text


# ══════════════════════════════════════════════════════════════
# Helper: paint a card background (white rounded rect + shadow)
# ══════════════════════════════════════════════════════════════
def paint_card(painter, rect, radius=8):
    """Draw a white card with a faint drop-shadow."""
    # shadow
    shadow = QRectF(rect.x() + 2, rect.y() + 2, rect.width(), rect.height())
    painter.setBrush(QColor(0, 0, 0, 25))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(shadow, radius, radius)
    # card
    painter.setBrush(BG_CARD)
    painter.setPen(QPen(GRID_LINE, 1))
    painter.drawRoundedRect(rect, radius, radius)
