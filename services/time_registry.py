"""Time Period Registry service for event-driven temporal synchronization across widgets."""

from typing import Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal
from models.time_context import TimeSpanContext


class TimePeriodRegistry(QObject):
    """Singleton broadcaster service that widgets subscribe to for time updates.

    When the global filter or time window changes, the application broadcasts
    a new ``TimeSpanContext`` through this registry. All subscribed widgets
    autonomously update their datasets and repaint without central controller intervention.
    """

    period_changed = pyqtSignal(TimeSpanContext)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._active_context: Optional[TimeSpanContext] = None

    def broadcast_period(self, context: TimeSpanContext) -> None:
        """Validate and broadcast a new time period context to all subscribed widgets."""
        self._active_context = context
        self.period_changed.emit(context)

    def get_active_context(self) -> Optional[TimeSpanContext]:
        """Return the currently active TimeSpanContext."""
        return self._active_context

    def subscribe(self, widget: Any) -> None:
        """Subscribe a TimeAware widget to receive period_changed signals immediately and on updates."""
        if hasattr(widget, "on_time_period_changed"):
            try:
                self.period_changed.connect(widget.on_time_period_changed)
            except TypeError:
                pass  # Already connected
            if self._active_context is not None:
                widget.on_time_period_changed(self._active_context)

    def unsubscribe(self, widget: Any) -> None:
        """Unsubscribe a widget from period_changed signals."""
        if hasattr(widget, "on_time_period_changed"):
            try:
                self.period_changed.disconnect(widget.on_time_period_changed)
            except (TypeError, RuntimeError):
                pass  # Not connected or already disconnected


# Singleton registry instance across the application
time_registry = TimePeriodRegistry()
