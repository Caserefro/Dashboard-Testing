"""
components.base
===============
Abstract base class hierarchy for all graphic widget components.

This module provides two core foundations:

1. :class:`BaseGraphicContainer` – The stateless visual card canvas (`QWidget`).
   It manages antialiased rendering, paints the rounded card background via
   `paint_card()`, and hooks into `showEvent`/`hideEvent` for `TimeAware` auto-subscription.
   Does not require a data model (`def __init__(self, parent=None)`), making it
   ideal for interactive UI containers (`PeriodFilterWidget`, `SqdpAspectChartWidget`).

2. :class:`BaseGraphicWidget` – The data-driven graphic widget (`Generic[T]`).
   Inherits `BaseGraphicContainer` and adds typed model storage (`self.model: T`)
   along with `set_data(model: T)` for live reactivity. Consumed by `BaseChartWidget`
   and `BaseTableWidget`.
"""

from __future__ import annotations

import abc
from typing import Any, Optional, TypeVar, Generic

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QRectF

from .theme import paint_card

T = TypeVar("T")

# Resolve metaclass conflict between QWidget (sip.wrappertype) and abc.ABCMeta:
_QABCMeta = type("_QABCMeta", (type(QWidget), abc.ABCMeta), {})


class BaseGraphicContainer(QWidget, metaclass=_QABCMeta):
    """Stateless visual card container that paints antialiased rounded cards.

    Zero `model` constructor parameter required (`parent=None`).
    Automatically subscribes/unsubscribes `TimeAware` mixin widgets on show/hide.
    """

    _CARD_MARGIN: int = 4
    _CARD_INSET: int = 12

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self._time_subscribed = False
        from .mixins import TimeAware
        if isinstance(self, TimeAware):
            from services.time_registry import time_registry
            time_registry.subscribe(self)
            self._time_subscribed = True

    # ── abstract ────────────────────────────────────────────────
    @abc.abstractmethod
    def paint_content(self, painter: QPainter, inner_rect: QRectF) -> None:
        """Paint the widget content inside *inner_rect*.

        Called automatically by :meth:`paintEvent` after the card
        background has been drawn. The painter already has antialiasing
        enabled. Implementations **must not** call ``painter.end()``.
        """

    # ── Qt override ─────────────────────────────────────────────
    def paintEvent(self, event: Any) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        m = self._CARD_MARGIN
        card = QRectF(m, m, w - m * 2 - 2, h - m * 2 - 2)
        paint_card(p, card)

        inset = self._CARD_INSET
        inner = card.adjusted(inset, inset, -inset, -inset)

        self.paint_content(p, inner)
        p.end()


class BaseGraphicWidget(BaseGraphicContainer, Generic[T]):
    """Abstract root widget for data-driven dashboard graphic components.

    Type Parameters
    ---------------
    T : dataclass
        The typed DTO that carries all data needed for rendering.

    Parameters
    ----------
    model : T
        Initial data model used for the first paint.
    parent : QWidget, optional
        Parent widget in the Qt object tree.
    """

    def __init__(self, model: T, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.model: T = model

    # ── public API ──────────────────────────────────────────────
    def set_data(self, model: T) -> None:
        """Replace the current model and schedule a repaint."""
        self.model = model
        self.update()
