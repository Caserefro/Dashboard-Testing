from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QRect

class FirstTimeYieldGaugeWidget(QWidget):
    """
    Pure Qt 5 radial/gauge widget for first_time_yield_gauge.
    Directly renders the percentage from pre-validated database records.
    """
    def __init__(self, fty_percentage: float, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.fty = fty_percentage
        self.setMinimumHeight(240)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setBrush(QColor("#1E1E1E"))
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.drawRoundedRect(rect, 8, 8)

        # Title
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect.adjusted(15, 12, -15, -15), Qt.AlignTop | Qt.AlignLeft, "First Time Yield (FTY) Gauge")

        # Gauge arc
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 3 - 10
        arc_rect = QRect(center.x() - radius, center.y() - radius + 15, radius * 2, radius * 2)

        # Background track (180 deg)
        painter.setPen(QPen(QColor("#3A3A3A"), 14, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(arc_rect, 0 * 16, 180 * 16)

        # Value track
        color = QColor("#00E676") if self.fty >= 90.0 else (QColor("#FFAB00") if self.fty >= 80.0 else QColor("#FF5252"))
        span_angle = int((self.fty / 100.0) * 180 * 16)
        painter.setPen(QPen(color, 14, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(arc_rect, (180 * 16) - span_angle, span_angle)

        # Text percent in center
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.setPen(color)
        painter.drawText(arc_rect, Qt.AlignCenter, f"{self.fty:.1f}%")


class ContractBarChartWidget(QWidget):
    """
    Pure Qt 5 bar chart widget for tickets_per_day_chart, burndown_curve, and safety_avg_chart.
    Directly renders category and value arrays from pre-validated database records without runtime checks.
    """
    def __init__(self, title: str, x_label: str, categories: List[str], values: List[float], color: QColor, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.x_label = x_label
        self.categories = categories
        self.values = values
        self.bar_color = color
        self.setMinimumHeight(240)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setBrush(QColor("#1E1E1E"))
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.drawRoundedRect(rect, 8, 8)

        # Title
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect.adjusted(15, 12, -15, -15), Qt.AlignTop | Qt.AlignLeft, self.title)

        if not self.categories or not self.values:
            return

        # Plot area
        plot_rect = rect.adjusted(45, 45, -25, -45)
        max_val = max(self.values) if max(self.values) > 0 else 10.0

        num_bars = len(self.categories)
        bar_width = min(40, int(plot_rect.width() / num_bars) - 12)
        spacing = (plot_rect.width() - (num_bars * bar_width)) // (num_bars + 1)

        painter.setFont(QFont("Segoe UI", 8))
        for i, (cat, val) in enumerate(zip(self.categories, self.values)):
            bar_h = int((val / max_val) * plot_rect.height())
            bx = plot_rect.left() + spacing + i * (bar_width + spacing)
            by = plot_rect.bottom() - bar_h

            # Draw bar
            painter.setBrush(self.bar_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(bx, by, bar_width, bar_h), 3, 3)

            # Draw label below
            painter.setPen(QColor("#AAAAAA"))
            painter.drawText(QRect(bx - 10, plot_rect.bottom() + 5, bar_width + 20, 20), Qt.AlignCenter, str(cat))

            # Draw value above
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(QRect(bx - 10, by - 20, bar_width + 20, 18), Qt.AlignCenter, f"{val:.1f}")


def create_graph_widget_from_data(graph_key: str, raw_data: List[Dict[str, Any]], parent: Optional[QWidget] = None) -> QWidget:
    """
    Direct factory function used by Presentation Layer (DashboardView).
    Instantiates pure Qt widgets immediately from data records without any runtime validation overhead,
    trusting that the Immutable Docker CI build gate verified the data offline.
    """
    if not raw_data:
        return QLabel(f"No data available for {graph_key}")

    if graph_key == "first_time_yield_gauge":
        fty = float(raw_data[0]["fty_percentage"])
        return FirstTimeYieldGaugeWidget(fty, parent)

    elif graph_key == "tickets_per_day_chart":
        cats = [row["day_label"] for row in raw_data]
        vals = [float(row["tickets_merged"]) for row in raw_data]
        return ContractBarChartWidget("Tickets Merged / Completed per Day", "Day of Week", cats, vals, QColor("#2979FF"), parent)

    elif graph_key == "safety_avg_chart":
        cats = [row["time_period"] for row in raw_data]
        vals = [float(row["safety_avg_score"]) for row in raw_data]
        return ContractBarChartWidget("Weekly Average Safety Score (%)", "Time Period", cats, vals, QColor("#00E676"), parent)

    elif graph_key == "burndown_curve":
        cats = [row["date"] for row in raw_data]
        rem = [float(row["remaining_points"]) for row in raw_data]
        return ContractBarChartWidget("Burndown Curve — Remaining Backlog Points", "Date", cats, rem, QColor("#FF6D00"), parent)

    return QLabel(f"Unknown graph key: {graph_key}")
