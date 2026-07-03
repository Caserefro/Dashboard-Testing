from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt, QRectF

# ══════════════════════════════════════════════════════════════
# Colour palette
# ══════════════════════════════════════════════════════════════
GREEN        = QColor("#4CAF50")
GREEN_LIGHT  = QColor("#66BB6A")
RED          = QColor("#F44336")
RED_LIGHT    = QColor("#EF5350")
ORANGE       = QColor("#FF9800")
ORANGE_BAR   = QColor("#F57C00")
NAVY         = QColor("#1A237E")
CELL_BORDER  = QColor("#333333")
TEXT_WHITE   = QColor("#FFFFFF")
BG_WHITE     = QColor("#FFFFFF")
BG_CARD      = QColor("#FFFFFF")
HEADER_CLR   = QColor("#212121")
SUBTEXT      = QColor("#757575")
GRID_LINE    = QColor("#E0E0E0")
TBL_HDR_BG   = QColor("#1565C0")
TBL_ALT_ROW  = QColor("#F5F5F5")
ACCENT_BLUE  = QColor("#1976D2")


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
