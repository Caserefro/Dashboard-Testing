"""
components.base
===============
Abstract base class for all graphic widget components.

Every graphic component in the dashboard inherits from
:class:`BaseGraphicWidget`.  It standardises:

* **Card background** – a rounded-rect card painted via ``paint_card()``.
* **Inner rectangle** – the usable area after card padding, passed to the
  subclass through :meth:`paint_content`.
* **Render hints** – antialiasing and text-antialiasing are always enabled.
* **Data model** – a generic typed data model stored in ``self.model`` and
  swappable at runtime via :meth:`set_data`.

Subclasses only need to override :meth:`paint_content` (or, for tables,
the higher-level ``paint_table`` method provided by ``BaseTableWidget``).
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


class BaseGraphicWidget(QWidget, Generic[T], metaclass=_QABCMeta):
    """Abstract root widget for every dashboard graphic component.

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

    Rendering Pipeline
    ------------------
    ``paintEvent`` →  paint card background  →  ``paint_content(painter, inner_rect)``

    Subclasses must implement :meth:`paint_content`.
    """

    _CARD_MARGIN: int = 4
    _CARD_INSET: int = 12

    def __init__(self, model: T, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.model: T = model

    # ── public API ──────────────────────────────────────────────
    def set_data(self, model: T) -> None:
        """Replace the current model and schedule a repaint."""
        self.model = model
        self.update()

    # ── abstract ────────────────────────────────────────────────
    @abc.abstractmethod
    def paint_content(self, painter: QPainter, inner_rect: QRectF) -> None:
        """Paint the widget content inside *inner_rect*.

        Called automatically by :meth:`paintEvent` after the card
        background has been drawn.  The painter already has antialiasing
        enabled.  Implementations **must not** call ``painter.end()``.
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
