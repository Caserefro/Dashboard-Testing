"""Component mixins for plug-and-play reactive behaviors."""

import abc
from models.time_context import TimeSpanContext


class TimeAware(abc.ABC):
    """Mixin that equips a widget with plug-and-play temporal reactivity.

    When a widget inherits from both a visual container/widget base (like
    BaseGraphicWidget) and TimeAware, it automatically subscribes to the
    global TimePeriodRegistry when shown and unsubscribes when hidden or
    destroyed.

    Subclasses MUST implement:
        on_time_period_changed(ctx: TimeSpanContext) -> None
    """

    @abc.abstractmethod
    def on_time_period_changed(self, ctx: TimeSpanContext) -> None:
        """Subscriber Slot: called autonomously whenever the active time period updates.

        Subclasses should build or fetch the updated domain model and call `self.set_data(...)`.
        """
        ...
