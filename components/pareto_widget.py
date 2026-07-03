from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF
from typing import Dict, Any, Optional

from .theme import HEADER_CLR, TEXT_WHITE, BG_WHITE, GRID_LINE, TBL_HDR_BG, TBL_ALT_ROW, paint_card

class ParetoWidget(QWidget):
    def __init__(self, table_data: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.table_data = table_data

    def set_data(self, data: Dict[str, Any]) -> None:
        self.table_data = data
        self.update()

    def paintEvent(self, event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        inner = card.adjusted(12, 12, -12, -12)

        weeks = self.table_data["weeks"]
        cats = self.table_data["categories"]
        n_data_cols = len(weeks) + 1          # +1 for Avg
        n_rows = 1 + len(cats)                # +1 for header
        
        if len(cats) == 0:
            p.end()
            return

        # ── column widths ──
        cat_col_w = inner.width() * 0.30
        data_col_w = (inner.width() - cat_col_w) / n_data_cols
        row_h = min(inner.height() / n_rows, 26)

        tx = inner.x()
        ty = inner.y()

        # ── header row ──
        hdr_font = QFont("Segoe UI", 8, QFont.Bold)
        p.setFont(hdr_font)

        # "Where Pareto" header cell
        hdr_rect = QRectF(tx, ty, cat_col_w, row_h)
        p.setBrush(TBL_HDR_BG)
        p.setPen(QPen(QColor("#0D47A1"), 1))
        p.drawRect(hdr_rect)
        p.setPen(TEXT_WHITE)
        p.drawText(hdr_rect.adjusted(6, 0, 0, 0),
                   Qt.AlignVCenter | Qt.AlignLeft, self.table_data["title"])

        # week header cells
        for j, wk in enumerate(weeks):
            rx = tx + cat_col_w + j * data_col_w
            r = QRectF(rx, ty, data_col_w, row_h)
            p.setBrush(TBL_HDR_BG)
            p.setPen(QPen(QColor("#0D47A1"), 1))
            p.drawRect(r)
            p.setPen(TEXT_WHITE)
            p.drawText(r, Qt.AlignCenter, str(wk))

        # "Avg" header cell
        ax = tx + cat_col_w + len(weeks) * data_col_w
        ar = QRectF(ax, ty, data_col_w, row_h)
        p.setBrush(TBL_HDR_BG)
        p.setPen(QPen(QColor("#0D47A1"), 1))
        p.drawRect(ar)
        p.setPen(TEXT_WHITE)
        p.drawText(ar, Qt.AlignCenter, "Avg")

        # ── data rows ──
        data_font = QFont("Segoe UI", 8)
        cat_font = QFont("Segoe UI", 8, QFont.Bold)
        for i, cat in enumerate(cats):
            ry = ty + (i + 1) * row_h
            row_bg = BG_WHITE if i % 2 == 0 else TBL_ALT_ROW

            # category cell
            cr = QRectF(tx, ry, cat_col_w, row_h)
            p.setBrush(row_bg)
            p.setPen(QPen(GRID_LINE, 0.8))
            p.drawRect(cr)
            p.setFont(cat_font)
            p.setPen(HEADER_CLR)
            p.drawText(cr.adjusted(6, 0, 0, 0),
                       Qt.AlignVCenter | Qt.AlignLeft, cat)

            # value cells
            p.setFont(data_font)
            for j in range(len(weeks)):
                rx = tx + cat_col_w + j * data_col_w
                r = QRectF(rx, ry, data_col_w, row_h)
                p.setBrush(row_bg)
                p.setPen(QPen(GRID_LINE, 0.8))
                p.drawRect(r)
                p.setPen(HEADER_CLR)
                val = self.table_data["values"][i][j]
                p.drawText(r, Qt.AlignCenter, str(val))

            # avg cell
            avr = QRectF(ax, ry, data_col_w, row_h)
            p.setBrush(row_bg)
            p.setPen(QPen(GRID_LINE, 0.8))
            p.drawRect(avr)
            p.setPen(HEADER_CLR)
            p.drawText(avr, Qt.AlignCenter, str(self.table_data["averages"][i]))

        p.end()
