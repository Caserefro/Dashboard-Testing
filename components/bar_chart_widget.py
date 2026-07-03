from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QLinearGradient
from PyQt5.QtCore import Qt, QRectF, QPointF
from typing import Dict, Any, Optional

from .theme import GREEN, RED, ORANGE_BAR, HEADER_CLR, SUBTEXT, GRID_LINE, paint_card

class BarChartWidget(QWidget):
    def __init__(self, chart_data: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.chart_data = chart_data

    def set_data(self, data: Dict[str, Any]) -> None:
        self.chart_data = data
        self.update()

    def paintEvent(self, event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        mg = {"top": 50, "bot": 40, "left": 44, "right": 16}
        cx = card.x() + mg["left"]
        cy = card.y() + mg["top"]
        cw = card.width() - mg["left"] - mg["right"]
        ch = card.height() - mg["top"] - mg["bot"]

        # ── title ──
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(HEADER_CLR)
        p.drawText(QRectF(card.x(), card.y() + 8, card.width(), 20),
                   Qt.AlignCenter, self.chart_data["title"])

        # ── legend boxes ──
        self._bar_legend(p, card)

        vals = self.chart_data["values"]
        n = len(vals)
        if n == 0:
            p.end()
            return
            
        y_max = 1.0

        # ── Y gridlines ──
        p.setFont(QFont("Segoe UI", 7))
        for i in range(11):
            v = i * 0.1
            yy = cy + ch - (v / y_max) * ch
            p.setPen(QPen(GRID_LINE, 0.5))
            p.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))
            if i % 2 == 0:
                p.setPen(SUBTEXT)
                p.drawText(QRectF(card.x() + 4, yy - 7, mg["left"] - 8, 14),
                           Qt.AlignRight | Qt.AlignVCenter, f"{v:.1f}")

        # ── threshold lines ──
        for thr, colour, lbl in [
            (self.chart_data["green_thr"], GREEN, ""),
            (self.chart_data["red_thr"], RED, ""),
        ]:
            yy = cy + ch - (thr / y_max) * ch
            pen = QPen(colour, 1.8, Qt.DashLine)
            p.setPen(pen)
            p.drawLine(QPointF(cx, yy), QPointF(cx + cw, yy))

        # ── bars ──
        bar_area = cw / n
        bar_w = bar_area * 0.65

        for i, v in enumerate(vals):
            bx = cx + i * bar_area + (bar_area - bar_w) / 2
            bh = (v / y_max) * ch
            by = cy + ch - bh
            rect = QRectF(bx, by, bar_w, bh)

            if v >= self.chart_data["green_thr"]:
                colour = GREEN
            elif v >= self.chart_data["red_thr"]:
                colour = ORANGE_BAR
            else:
                colour = RED

            grad = QLinearGradient(QPointF(bx, by), QPointF(bx, by + bh))
            grad.setColorAt(0, colour.lighter(115))
            grad.setColorAt(1, colour)
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(rect, 2, 2)

            # x label
            p.setPen(HEADER_CLR)
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRectF(bx - 2, cy + ch + 3, bar_w + 4, 14),
                       Qt.AlignCenter, str(self.chart_data["weeks"][i]))

        # ── x-axis label ──
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(SUBTEXT)
        p.drawText(QRectF(cx, cy + ch + 18, cw, 16),
                   Qt.AlignCenter, self.chart_data["x_label"])

        p.end()

    def _bar_legend(self, p: QPainter, card: QRectF) -> None:
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        bx = 10
        ly = card.y() + 30
        for colour, lbl, dx in [
            (GREEN, f"Green >= {self.chart_data['green_thr']}", card.width() - 170),
            (RED, f"Red < {self.chart_data['red_thr']}", card.width() - 85),
        ]:
            x = card.x() + dx
            p.setBrush(colour)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(x, ly, bx, bx), 2, 2)
            p.setPen(HEADER_CLR)
            p.drawText(QRectF(x + bx + 3, ly - 1, 70, 14),
                       Qt.AlignVCenter | Qt.AlignLeft, lbl)
