from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QLinearGradient
from PyQt5.QtCore import Qt, QRectF, QPointF
from typing import List, Dict, Any, Optional

from .theme import GREEN, GREEN_LIGHT, RED, RED_LIGHT, HEADER_CLR, TEXT_WHITE, SUBTEXT, CELL_BORDER, paint_card

class SQDPWidget(QWidget):
    def __init__(self, sqdp_data: List[Dict[str, Any]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.sqdp_data = sqdp_data

    def set_data(self, data: List[Dict[str, Any]]) -> None:
        self.sqdp_data = data
        self.update()

    def paintEvent(self, event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        inner = card.adjusted(10, 10, -10, -10)
        n = len(self.sqdp_data)
        if n == 0:
            p.end()
            return
            
        sec_w = inner.width() / n
        top_y = inner.y() + 4

        for idx, ltr in enumerate(self.sqdp_data):
            cx = inner.x() + sec_w * idx + sec_w / 2
            self._draw_letter(p, ltr, cx, top_y, sec_w * 0.90, inner.height() - 10)

        self._legend(p, inner)
        p.end()

    def _draw_letter(self, p: QPainter, ltr: Dict[str, Any], cx: float, y_top: float, max_w: float, max_h: float) -> None:
        rows, cols = ltr["rows"], ltr["cols"]
        csz = min(max_w / (cols + 0.4), (max_h - 50) / (rows + 0.4), 38)
        gw = cols * csz
        gh = rows * csz
        gx = cx - gw / 2
        gy = y_top + 26

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(HEADER_CLR)
        p.drawText(QRectF(gx - 10, y_top, gw + 20, 22),
                   Qt.AlignCenter, ltr["label"])

        cell_map = {(r, c): i for i, (r, c) in enumerate(ltr["cells"])}
        nf = QFont("Segoe UI", max(7, int(csz * 0.28)), QFont.Bold)

        for (r, c), idx in cell_map.items():
            rx = gx + c * csz
            ry = gy + r * csz
            rect = QRectF(rx + 1, ry + 1, csz - 2, csz - 2)
            ok = ltr["status"][idx]
            base, light = (GREEN, GREEN_LIGHT) if ok else (RED, RED_LIGHT)
            grad = QLinearGradient(QPointF(rx, ry), QPointF(rx, ry + csz))
            grad.setColorAt(0, light)
            grad.setColorAt(1, base)
            p.setBrush(grad)
            p.setPen(QPen(CELL_BORDER, 1.2))
            p.drawRoundedRect(rect, 2, 2)
            p.setFont(nf)
            p.setPen(TEXT_WHITE)
            p.drawText(rect, Qt.AlignCenter, str(idx + 1))

        total = len(ltr["cells"])
        gn = sum(ltr["status"])
        pct = int(gn / total * 100) if total else 0
        p.setFont(QFont("Segoe UI", 7))
        p.setPen(SUBTEXT)
        p.drawText(QRectF(gx - 15, gy + gh + 3, gw + 30, 16),
                   Qt.AlignCenter, f"{gn}/{total} ({pct}%)")

    def _legend(self, p: QPainter, inner: QRectF) -> None:
        bx = 12
        ly = inner.bottom() - 16
        lx = inner.right() - 230
        p.setFont(QFont("Segoe UI", 7))
        for colour, label, dx in [(GREEN, "On Target", 0),
                                   (RED, "Needs Attention", 100)]:
            p.setBrush(colour)
            p.setPen(QPen(CELL_BORDER, 0.8))
            p.drawRoundedRect(QRectF(lx + dx, ly, bx, bx), 2, 2)
            p.setPen(HEADER_CLR)
            p.drawText(QRectF(lx + dx + bx + 4, ly - 1, 90, 16),
                       Qt.AlignVCenter | Qt.AlignLeft, label)
