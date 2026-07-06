"""
components.tables.safety.safety_table_focal
===========================================
Safety table for focal point review and investigation.

Purpose
-------
Extends the read-only :class:`SafetyTable` with a fifth *Status*
column that displays coloured review-status badges.  This gives
focal-point reviewers an at-a-glance view of which safety items
have been handled and which still need attention.

Status badges
-------------
* **Pending** — yellow badge (``#FFC107``).
* **Reviewed** — green badge (``#4CAF50``).
* **Escalated** — red badge (``#F44336``).

Any other status value falls back to a neutral grey badge.

This widget performs **no** workflow logic.  The ``status`` value
for each field is read from the ``SafetyFieldModel.comment`` field
(or from a dedicated attribute if the model is extended later).  By
default, the focal table interprets the *comment* string as the
review status when it matches one of the known status keywords;
otherwise it renders the comment as-is in the Comment column and
shows "Pending" in the Status column.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

from components.theme import (
    HEADER_CLR,
    TEXT_WHITE,
    GRID_LINE,
    BG_WHITE,
    TBL_ALT_ROW,
    GREEN,
    RED,
)
from components.tables.base_table import BaseTableWidget
from components.tables.safety.safety_table import SafetyTable, SafetyTableModel

# ── constants ───────────────────────────────────────────────────
_FOCAL_HEADERS = ["Field", "Value", "Category", "Comment", "Status"]
_FOCAL_RATIOS = (0.22, 0.16, 0.16, 0.26, 0.20)  # 5 columns, sum = 1.0
_MAX_ROW_H = 26

_BADGE_FONT = QFont("Segoe UI", 7, QFont.Bold)
_DATA_FONT = QFont("Segoe UI", 8)
_SUB_HDR_FONT = QFont("Segoe UI", 8, QFont.Bold)
_SUB_HDR_BG = QColor("#E3F2FD")

_STATUS_COLOURS: Dict[str, QColor] = {
    "pending": QColor("#FFC107"),    # amber / yellow
    "reviewed": GREEN,               # green
    "escalated": RED,                # red
}
_STATUS_DEFAULT = QColor("#9E9E9E")  # grey fallback

# Known status keywords (case-insensitive)
_STATUS_KEYWORDS = {"pending", "reviewed", "escalated"}


class SafetyTableFocal(SafetyTable):
    """Safety table for focal point review and investigation.

    Extends :class:`SafetyTable` with a fifth *Status* column showing
    coloured badges for ``Pending``, ``Reviewed``, or ``Escalated``.

    Status resolution
    -----------------
    If a field's ``comment`` matches a known status keyword (case-
    insensitive), it is used as the status and the Comment column shows
    ``"—"``.  Otherwise the comment is shown as-is and the status
    defaults to ``"Pending"``.

    Parameters
    ----------
    model : SafetyTableModel
        Initial table data.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        model: SafetyTableModel,
        parent: Optional[Any] = None,
    ) -> None:
        super().__init__(model, parent)

    # ── column widths (5 columns) ───────────────────────────────
    @staticmethod
    def _col_widths(total_w: float) -> List[float]:  # type: ignore[override]
        """Return absolute column widths for the 5-column focal layout."""
        return [total_w * r for r in _FOCAL_RATIOS]

    # ── status resolution ───────────────────────────────────────
    @staticmethod
    def _resolve_status(comment: str) -> tuple[str, str]:
        """Return ``(display_comment, status_label)`` from *comment*.

        If the comment is a known status keyword, the comment column
        shows ``"—"`` and the keyword becomes the status.  Otherwise
        the comment is passed through and the status defaults to
        ``"Pending"``.
        """
        stripped = comment.strip().lower()
        if stripped in _STATUS_KEYWORDS:
            return "—", stripped.capitalize()
        return comment, "Pending"

    # ── rendering ───────────────────────────────────────────────
    def paint_table(self, painter: QPainter, inner: QRectF) -> None:
        """Paint the 5-column focal review table inside *inner*."""
        m = self.model
        n_rows = 1 + len(m.fields)
        row_h = min(inner.height() / max(n_rows, 1), _MAX_ROW_H)
        widths = self._col_widths(inner.width())
        tx, ty = inner.x(), inner.y()

        # ── header row ─────────────────────────────────────────
        x = tx
        for idx, hdr in enumerate(_FOCAL_HEADERS):
            self._draw_header_cell(painter, QRectF(x, ty, widths[idx], row_h), hdr)
            x += widths[idx]

        # ── data rows ─────────────────────────────────────────
        for i, fld in enumerate(m.fields):
            ry = ty + (i + 1) * row_h
            display_comment, status_label = self._resolve_status(fld.comment)
            x = tx

            texts = [fld.field_name, fld.field_value, fld.category, display_comment]
            for col_idx, txt in enumerate(texts):
                cell = QRectF(x, ry, widths[col_idx], row_h)

                if col_idx == 2:
                    # Category badge
                    self._draw_data_cell(painter, cell, "", i)
                    self._draw_badge(painter, cell, txt)
                else:
                    align = Qt.AlignLeft if col_idx in (0, 3) else Qt.AlignCenter
                    self._draw_data_cell(
                        painter, cell, txt, i,
                        bold=(col_idx == 0),
                        align=align,
                    )
                x += widths[col_idx]

            # Status badge in the 5th column
            status_cell = QRectF(x, ry, widths[4], row_h)
            self._draw_data_cell(painter, status_cell, "", i)
            self._draw_status_badge(painter, status_cell, status_label)

    # ── status badge ────────────────────────────────────────────
    @staticmethod
    def _draw_status_badge(
        p: QPainter,
        cell: QRectF,
        status: str,
    ) -> None:
        """Draw a coloured status badge centred in *cell*.

        Parameters
        ----------
        p : QPainter
            Active painter.
        cell : QRectF
            The cell in which the badge is centred.
        status : str
            Status label — ``"Pending"``, ``"Reviewed"``, or
            ``"Escalated"``.  Unknown values fall back to grey.
        """
        colour = _STATUS_COLOURS.get(status.lower(), _STATUS_DEFAULT)

        p.setFont(_BADGE_FONT)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(status) + 14
        th = fm.height() + 4
        bx = cell.center().x() - tw / 2
        by = cell.center().y() - th / 2
        badge_rect = QRectF(bx, by, tw, th)

        p.setBrush(colour)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(badge_rect, 3, 3)

        p.setPen(TEXT_WHITE)
        p.drawText(badge_rect, Qt.AlignCenter, status)
