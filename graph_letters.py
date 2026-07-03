"""
WOR Dashboard — Combined SQDP + Productivity Chart + Where Pareto
Pure PyQt5 implementation — Demo version
"""
import sys
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QLinearGradient, QBrush,
)
from PyQt5.QtCore import Qt, QRectF, QPointF


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
# Data — SQDP letters
# ══════════════════════════════════════════════════════════════
LETTERS = [
    {
        "char": "S", "label": "Safety",
        "rows": 7, "cols": 4,
        "cells": [
            (0, 3), (0, 2), (0, 1),
            (1, 0), (2, 0),
            (3, 1), (3, 2), (3, 3),
            (4, 3), (5, 3),
            (6, 2), (6, 1), (6, 0),
        ],
        "status": [0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    },
    {
        "char": "Q", "label": "Quality",
        "rows": 7, "cols": 5,
        "cells": [
            (0, 1), (0, 2), (0, 3),
            (1, 4), (2, 4), (3, 4),
            (4, 3), (4, 2), (4, 1),
            (3, 0), (2, 0), (1, 0),
            (5, 4),
        ],
        "status": [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
    },
    {
        "char": "D", "label": "Delivery",
        "rows": 6, "cols": 5,
        "cells": [
            (0, 0), (0, 1), (0, 2), (0, 3),
            (1, 4), (2, 4), (3, 4),
            (4, 3), (4, 2), (4, 1), (4, 0),
            (3, 0), (2, 0), (1, 0),
        ],
        "status": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
    {
        "char": "P", "label": "Productivity",
        "rows": 7, "cols": 4,
        "cells": [
            (3, 3), (2, 3), (1, 3),
            (0, 3), (0, 2), (0, 1), (0, 0),
            (1, 0), (2, 0), (3, 0),
            (4, 0), (5, 0), (6, 0),
        ],
        "status": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    },
]


# ══════════════════════════════════════════════════════════════
# Data — Productivity bar chart
# ══════════════════════════════════════════════════════════════
BAR_CHART = {
    "title": "Productivity : How efficient are we being?",
    "x_label": "Weeks",
    "weeks": list(range(1, 14)),
    "values": [
        0.75, 0.82, 0.68, 0.91, 0.85,
        0.79, 0.88, 0.72, 0.95, 0.81,
        0.77, 0.90, 0.86,
    ],
    "green_thr": 0.8,
    "red_thr": 0.6,
}


# ══════════════════════════════════════════════════════════════
# Data — Where Pareto table
# ══════════════════════════════════════════════════════════════
PARETO = {
    "title": "Where Pareto",
    "weeks": [13, 14, 15, 16, 17, 18, 19],
    "categories": [
        "Support",
        "Mg availability",
        "Mg performance",
        "Task Planning",
        "Work Standards",
        "Training Needs",
        "Input Delays",
        "Input Quality",
    ],
    "values": [[0] * 7 for _ in range(8)],
    "averages": [0] * 8,
}


# ══════════════════════════════════════════════════════════════
# Data — ESC-A Verification Progress Inc. Year
# ══════════════════════════════════════════════════════════════
_weeks_esc = list(range(14, 39))  # weeks 14–38
_weekly = [
    120, 135, 110, 145, 160, 95, 155, 140, 125, 150,
    105, 140, 130, 165, 115, 138, 155, 120, 145, 100,
    150, 130, 115, 140, 125,
]
_completed = [
    280, 290, 295, 305, 315, 318, 325, 332, 338, 345,
    350, 355, 358, 362, 365, 370, 374, 378, 382, 386,
    390, 394, 397, 400, 405,
]
_total = [
    350, 358, 365, 372, 380, 387, 395, 402, 410, 418,
    425, 432, 440, 447, 455, 460, 465, 470, 475, 478,
    482, 485, 488, 492, 495,
]

ESC_CHART = {
    "title": "ESC-A Verification Progress Inc. Year",
    "x_label": "Quarter",
    "weeks": _weeks_esc,
    "weekly": _weekly,
    "completed": _completed,
    "total": _total,
    "y_max": 500,
}


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


# ╔════════════════════════════════════════════════════════════╗
# ║  SQDP Letter-Diagram Widget                               ║
# ╚════════════════════════════════════════════════════════════╝
class SQDPWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        inner = card.adjusted(10, 10, -10, -10)
        n = len(LETTERS)
        sec_w = inner.width() / n
        top_y = inner.y() + 4

        for idx, ltr in enumerate(LETTERS):
            cx = inner.x() + sec_w * idx + sec_w / 2
            self._draw_letter(p, ltr, cx, top_y, sec_w * 0.90, inner.height() - 10)

        # legend
        self._legend(p, inner)
        p.end()

    # ── single letter ──────────────────────────────────────
    def _draw_letter(self, p, ltr, cx, y_top, max_w, max_h):
        rows,   cols = ltr["rows"], ltr["cols"]
        csz = min(max_w / (cols + 0.4), (max_h - 50) / (rows + 0.4), 38)
        gw = cols * csz
        gh = rows * csz
        gx = cx - gw / 2
        gy = y_top + 26

        # label
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

        # score
        total = len(ltr["cells"])
        gn = sum(ltr["status"])
        pct = int(gn / total * 100) if total else 0
        p.setFont(QFont("Segoe UI", 7))
        p.setPen(SUBTEXT)
        p.drawText(QRectF(gx - 15, gy + gh + 3, gw + 30, 16),
                   Qt.AlignCenter, f"{gn}/{total} ({pct}%)")

    # ── legend ─────────────────────────────────────────────
    def _legend(self, p, inner):
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


# ╔════════════════════════════════════════════════════════════╗
# ║  Productivity Bar-Chart Widget                             ║
# ╚════════════════════════════════════════════════════════════╝
class BarChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def paintEvent(self, event):
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
                   Qt.AlignCenter, BAR_CHART["title"])

        # ── legend boxes ──
        self._bar_legend(p, card)

        vals = BAR_CHART["values"]
        n = len(vals)
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
            (BAR_CHART["green_thr"], GREEN, f"Green >= {BAR_CHART['green_thr']}"),
            (BAR_CHART["red_thr"], RED, f"Red < {BAR_CHART['red_thr']}"),
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

            if v >= BAR_CHART["green_thr"]:
                colour = GREEN
            elif v >= BAR_CHART["red_thr"]:
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
                       Qt.AlignCenter, str(BAR_CHART["weeks"][i]))

        # ── x-axis label ──
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(SUBTEXT)
        p.drawText(QRectF(cx, cy + ch + 18, cw, 16),
                   Qt.AlignCenter, BAR_CHART["x_label"])

        p.end()

    def _bar_legend(self, p, card):
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        bx = 10
        ly = card.y() + 30
        for colour, lbl, dx in [
            (GREEN, f"Green >= {BAR_CHART['green_thr']}", card.width() - 170),
            (RED, f"Red < {BAR_CHART['red_thr']}", card.width() - 85),
        ]:
            x = card.x() + dx
            p.setBrush(colour)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(x, ly, bx, bx), 2, 2)
            p.setPen(HEADER_CLR)
            p.drawText(QRectF(x + bx + 3, ly - 1, 70, 14),
                       Qt.AlignVCenter | Qt.AlignLeft, lbl)


# ╔════════════════════════════════════════════════════════════╗
# ║  Where Pareto Table Widget                                 ║
# ╚════════════════════════════════════════════════════════════╝
class ParetoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()

        card = QRectF(4, 4, w - 10, h - 10)
        paint_card(p, card)

        inner = card.adjusted(12, 12, -12, -12)

        weeks = PARETO["weeks"]
        cats = PARETO["categories"]
        n_data_cols = len(weeks) + 1          # +1 for Avg
        n_cols = 1 + n_data_cols              # +1 for category name
        n_rows = 1 + len(cats)                # +1 for header

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
                   Qt.AlignVCenter | Qt.AlignLeft, PARETO["title"])

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
                val = PARETO["values"][i][j]
                p.drawText(r, Qt.AlignCenter, str(val))

            # avg cell
            avr = QRectF(ax, ry, data_col_w, row_h)
            p.setBrush(row_bg)
            p.setPen(QPen(GRID_LINE, 0.8))
            p.drawRect(avr)
            p.setPen(HEADER_CLR)
            p.drawText(avr, Qt.AlignCenter, str(PARETO["averages"][i]))

        p.end()


# ╔════════════════════════════════════════════════════════════╗
# ║  ESC-A Verification Progress Combo Chart                   ║
# ╚════════════════════════════════════════════════════════════╝
class ESCChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def paintEvent(self, event):
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
                   Qt.AlignCenter, ESC_CHART["title"])

        weeks = ESC_CHART["weeks"]
        weekly = ESC_CHART["weekly"]
        completed = ESC_CHART["completed"]
        total = ESC_CHART["total"]
        y_max = ESC_CHART["y_max"]
        n = len(weeks)

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
        def pt(i, val):
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
                   Qt.AlignCenter, ESC_CHART["x_label"])

        # ── legend ──
        self._legend(p, card)
        p.end()

    def _legend(self, p, card):
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


# ╔════════════════════════════════════════════════════════════╗
# ║  Main Window                                               ║
# ╚════════════════════════════════════════════════════════════╝
class WORDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WOR Dashboard")
        self.resize(1280, 720)
        self.setStyleSheet("QMainWindow { background: #ECEFF1; }")

        # ── central ──
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 6, 10, 4)
        root.setSpacing(4)

        # ── header ──
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                         stop:0 #1A237E, stop:1 #1565C0);
            border-radius: 6px;
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 0, 16, 0)

        team_lbl = QLabel("TeamName_DPT_202X")
        team_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        team_lbl.setStyleSheet("color: #BBDEFB;")

        title_lbl = QLabel("WOR Dashboard")
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_lbl.setStyleSheet("color: white;")
        title_lbl.setAlignment(Qt.AlignCenter)

        quarter_lbl = QLabel("Quarter 1")
        quarter_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        quarter_lbl.setStyleSheet("color: #BBDEFB;")
        quarter_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        hdr_lay.addWidget(team_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()
        hdr_lay.addWidget(quarter_lbl)

        root.addWidget(hdr)

        # ── grid of widgets ──
        grid = QGridLayout()
        grid.setSpacing(6)

        sqdp = SQDPWidget()
        chart = BarChartWidget()
        pareto = ParetoWidget()

        # ESC-A chart bottom-left
        esc_chart = ESCChartWidget()

        grid.addWidget(sqdp,        0, 0)
        grid.addWidget(chart,       0, 1)
        grid.addWidget(esc_chart,   1, 0)
        grid.addWidget(pareto,      1, 1)

        grid.setColumnStretch(0, 55)
        grid.setColumnStretch(1, 45)
        grid.setRowStretch(0, 58)
        grid.setRowStretch(1, 42)

        root.addLayout(grid, 1)

        # ── footer ──
        footer = QLabel("Visual Management")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont("Segoe UI", 9, QFont.Bold))
        footer.setStyleSheet("color: #546E7A; padding: 2px;")
        root.addWidget(footer)

        # ── status bar ──
        total = sum(len(l["cells"]) for l in LETTERS)
        green = sum(sum(l["status"]) for l in LETTERS)
        pct = int(green / total * 100) if total else 0
        today = date.today().strftime("%A, %B %d, %Y")
        self.statusBar().showMessage(
            f"  {today}  •  Overall SQDP: {green}/{total} on target — {pct}%"
        )
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #263238; color: #B0BEC5; font-size: 11px; }"
        )


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WORDashboard()
    win.show()
    sys.exit(app.exec_())
