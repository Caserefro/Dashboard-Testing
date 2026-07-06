"""SQDP board data models.

Dataclass DTOs that describe the Safety-Quality-Delivery-Productivity
letter-diagram widget.  Each letter is a shaped grid of cells whose
status values (1 = on target, 0 = needs attention) are rendered by
the graphic component without any business-logic transformation.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SqdpLetterModel:
    """Data model for a single SQDP letter (S, Q, D, or P).

    Represents one letter in the SQDP board.  Each letter is rendered
    as a grid of cells where each cell's status indicates whether the
    corresponding day/metric met its target.

    Attributes:
        char: Single character identifier ('S', 'Q', 'D', or 'P').
        label: Human-readable label ('Safety', 'Quality', 'Delivery',
               'Productivity').
        rows: Number of rows in the letter's grid shape.
        cols: Number of columns in the letter's grid shape.
        cells: List of (row, col) coordinates that form the letter shape.
        status: List of integers (1=on target, 0=needs attention)
                parallel to *cells*.
    """

    char: str
    label: str
    rows: int
    cols: int
    cells: List[Tuple[int, int]]
    status: List[int]

    def __post_init__(self) -> None:
        if len(self.cells) != len(self.status):
            raise ValueError(
                f"SqdpLetterModel '{self.char}' mismatch: cells ({len(self.cells)}) "
                f"vs status ({len(self.status)}) must be equal length."
            )


@dataclass
class SqdpBoardModel:
    """Complete data model for an SQDP board.

    Encapsulates all four SQDP letters and the time-range context.
    The graphic widget receives this model and renders it without
    performing any calculations.

    Attributes:
        title: Display title for the board.
        time_range: One of ``'daily'`` (31 cells),
                    ``'sprint_1w'`` (7 cells),
                    ``'sprint_2w'`` (14 cells).
        letters: List of :class:`SqdpLetterModel` instances
                 (typically 4: S, Q, D, P).
    """

    title: str
    time_range: str
    letters: List[SqdpLetterModel] = field(default_factory=list)
