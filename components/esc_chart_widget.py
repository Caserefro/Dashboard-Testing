from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QRectF, QPointF
from typing import Dict, Any, Optional

from .theme import ACCENT_BLUE, HEADER_CLR, SUBTEXT, GRID_LINE, paint_card

class ESCChartWidget(QWidget):
    def __init__(self, combo_data: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.combo_data = combo_data

    def set_data(self, data: Dict[str, Any]) -> None:
        self.combo_data = data
        self.update()

    def paintEvent(self, event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        mg = {"top": 40, "bot": 38, "left": 44, "right": 16}
        cx = card.x() + mg["left"]
        cy = card.y() + mg["top"]
        cw = card.width() - mg["left"] - mg["right"]
        ch = card.height() - mg["top"] - mg["bot"]

        if cw <= 0 or ch <= 0:
            p.end()
            return

        # ── title ──
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(HEADER_CLR)
        p.drawText(QRectF(card.x(), card.y() + 8, card.width(), 18),
                   Qt.AlignCenter, self.combo_data["title"])

        weeks = self.combo_data["weeks"]
        weekly = self.combo_data["weekly"]
        completed = self.combo_data["completed"]
        total = self.combo_data["total"]
        y_max = self.combo_data["y_max"]
        n = len(weeks)
        if n == 0:
            p.end()
            return

        # ── Y gridlines + labels ──
        p.setFont(QFont("Segoe UI", 6))
        for v in range(0, y_max + 1, 50):
            yy = cy + ch - (v / y_max) * ch
            p.setPen(QPen(GRID_LINE, 0.5))
            p.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))
            if v % 100 == 0:
                p.setPen(SUBTEXT)
                p.drawText(QRectF(card.x() + 2, yy - 6, mg["left"] - 6, 12),
                           Qt.AlignRight | Qt.AlignVCenter, str(v))

        # ── bars (weekly values) ──
        slot_w = cw / n
        bar_w = slot_w * 0.55
        for i, v in enumerate(weekly):
            bx = cx + i * slot_w + (slot_w - bar_w) / 2
            bh = (v / y_max) * ch
            by = cy + ch - bh
            rect = QRectF(bx, by, bar_w, bh)
            grad = QLinearGradient(QPointF(bx, by), QPointF(bx, by + bh))
            grad.setColorAt(0, ACCENT_BLUE.lighter(140))
            grad.setColorAt(1, ACCENT_BLUE)
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(rect, 1, 1)

        # ── helper: data index → pixel point ──
        def pt(i: int, val: float) -> QPointF:
            x = cx + i * slot_w + slot_w / 2
            y = cy + ch - (val / y_max) * ch
            return QPointF(x, y)

        # ── line: Completed_3P (solid black) ──
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#212121"), 2.0, Qt.SolidLine))
        for i in range(n - 1):
            p.drawLine(pt(i, completed[i]), pt(i + 1, completed[i + 1]))
        p.setBrush(QColor("#212121"))
        p.setPen(QPen(QColor("#212121"), 1))
        for i in range(n):
            p.drawEllipse(pt(i, completed[i]), 2.5, 2.5)

        # ── line: Total_3P (dashed blue) ──
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(ACCENT_BLUE, 2.0, Qt.DashLine))
        for i in range(n - 1):
            p.drawLine(pt(i, total[i]), pt(i + 1, total[i + 1]))
        p.setBrush(ACCENT_BLUE)
        p.setPen(QPen(ACCENT_BLUE, 1))
        for i in range(n):
            p.drawEllipse(pt(i, total[i]), 2.5, 2.5)

        # ── X labels ──
        p.setFont(QFont("Segoe UI", 6))
        p.setPen(HEADER_CLR)
        for i, wk in enumerate(weeks):
            lx = cx + i * slot_w
            p.drawText(QRectF(lx, cy + ch + 2, slot_w, 12),
                       Qt.AlignCenter, str(wk))

        p.setFont(QFont("Segoe UI", 7))
        p.setPen(SUBTEXT)
        p.drawText(QRectF(cx, cy + ch + 14, cw, 14),
                   Qt.AlignCenter, self.combo_data["x_label"])

        # ── legend ──
        self._legend(p, card)
        p.end()

    def _legend(self, p: QPainter, card: QRectF) -> None:
        ly = card.y() + 26
        lx = card.x() + 14
        seg = 20
        p.setFont(QFont("Segoe UI", 7))

        # Completed_3P — solid black line
        p.setPen(QPen(QColor("#212121"), 2, Qt.SolidLine))
        p.drawLine(QPointF(lx, ly + 5), QPointF(lx + seg, ly + 5))
        p.setPen(HEADER_CLR)
        p.drawText(QRectF(lx + seg + 4, ly - 2, 90, 14),
                   Qt.AlignVCenter | Qt.AlignLeft, "Completed_3P")

        # Total_3P — dashed blue line
        off = 120
        p.setPen(QPen(ACCENT_BLUE, 2, Qt.DashLine))
        p.drawLine(QPointF(lx + off, ly + 5), QPointF(lx + off + seg, ly + 5))
        p.setPen(HEADER_CLR)
        p.drawText(QRectF(lx + off + seg + 4, ly - 2, 90, 14),
                   Qt.AlignVCenter | Qt.AlignLeft, "Total_3P")
