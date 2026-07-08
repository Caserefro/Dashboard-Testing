import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QRectF


class BarChartWidget(QWidget):
    def __init__(self, spec: dict, parent=None):
        super().__init__(parent)
        self.spec = spec
        self.setMinimumSize(300, 200)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        margin = {"top": 40, "bottom": 50, "left": 60, "right": 20}
        chart_w = w - margin["left"] - margin["right"]
        chart_h = h - margin["top"] - margin["bottom"]

        # Title
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(QRectF(0, 5, w, 30), Qt.AlignCenter, self.spec["title"])

        categories = self.spec["categories"]
        all_series = self.spec["series"]
        n_cats = len(categories)
        n_series = len(all_series)
        if n_cats == 0:
            return

        # Compute Y scale
        all_vals = [v for s in all_series for v in s["values"]]
        y_max = max(all_vals) * 1.1 if all_vals else 1

        # Draw bars
        group_w = chart_w / n_cats
        bar_w = group_w * 0.7 / n_series
        gap = group_w * 0.15

        for i, cat in enumerate(categories):
            x_group = margin["left"] + i * group_w
            for j, series in enumerate(all_series):
                val = series["values"][i]
                bar_h = (val / y_max) * chart_h
                x = x_group + gap + j * bar_w
                y = margin["top"] + chart_h - bar_h

                p.setBrush(QColor(series["color"]))
                p.setPen(Qt.NoPen)
                p.drawRect(QRectF(x, y, bar_w - 2, bar_h))

            # Category label
            p.setPen(Qt.black)
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(x_group, h - margin["bottom"] + 5,
                              group_w, 20), Qt.AlignCenter, cat)

        # Threshold lines
        for th in self.spec.get("thresholds", []):
            y_pos = margin["top"] + chart_h - (th["value"] / y_max) * chart_h
            pen = QPen(QColor(th["color"]), 2, Qt.DashLine)
            p.setPen(pen)
            p.drawLine(margin["left"], int(y_pos), w - margin["right"], int(y_pos))

        p.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sample data to test with
    sample_spec = {
        "title": "Productivity: How efficient are we being?",
        "categories": [f"S{i}" for i in range(1, 14)],
        "series": [
            {
                "name": "Actual",
                "color": "#F57C00",
                "values": [0.75, 0.82, 0.68, 0.91, 0.85, 0.79, 0.88, 0.72, 0.95, 0.81, 0.77, 0.90, 0.86],
            },
        ],
        "thresholds": [
            {"value": 0.8, "color": "#4CAF50", "label": "Green >= 0.8"},
            {"value": 0.6, "color": "#F44336", "label": "Red < 0.6"},
        ],
    }

    window = BarChartWidget(sample_spec)
    window.setWindowTitle("Bar Chart Test")
    window.resize(700, 400)
    window.show()

    sys.exit(app.exec_())
