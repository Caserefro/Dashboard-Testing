"""Table data models.

Dataclass DTOs for table-style graphic components: Pareto
loss-analysis tables and physiological-safety tables.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ParetoTableModel:
    """Data model for a Pareto loss-analysis table.

    Displays loss categories across time periods (weeks) with an
    average column.  Used in daily management to identify top
    contributors to inefficiency.

    Attributes:
        title: Table title displayed in the header cell.
        categories: List of loss category names (row labels).
        columns: List of column headers (e.g. week numbers as strings).
        values: 2-D list ``[row][col]`` of numeric values.
        averages: List of average values, one per category row.
    """

    title: str
    categories: List[str]
    columns: List[str]
    values: List[List[float]]
    averages: List[float]

    def __post_init__(self) -> None:
        if len(self.values) != len(self.categories) or len(self.averages) != len(self.categories):
            raise ValueError(
                f"ParetoTableModel mismatch: categories ({len(self.categories)}), "
                f"values ({len(self.values)}), averages ({len(self.averages)}) must be equal length."
            )
        for r, row_vals in enumerate(self.values):
            if len(row_vals) != len(self.columns):
                raise ValueError(
                    f"ParetoTableModel row {r} length ({len(row_vals)}) "
                    f"does not match columns ({len(self.columns)})."
                )


@dataclass
class SafetyFieldModel:
    """Data model for a single field in the safety table.

    Represents one safety concern or metric entry.

    Attributes:
        field_name: Name of the safety field / aspect.
        field_value: Current value or description.
        category: Classification category
                  (e.g. ``'Ergonomic'``, ``'Chemical'``).
        comment: Optional comment or note.
    """

    field_name: str
    field_value: str
    category: str
    comment: str = ''


@dataclass
class SafetyTableModel:
    """Data model for a physiological safety metrics table.

    Displays safety fields with their values, categories, and
    comments.  Used by different role-based views (user, focal,
    admin).

    Attributes:
        title: Table title displayed in the header.
        principal: Name of the safety principal / responsible person.
        categories: List of safety-category classifications.
        fields: List of :class:`SafetyFieldModel` entries.
    """

    title: str
    principal: str
    categories: List[str]
    fields: List[SafetyFieldModel] = field(default_factory=list)


@dataclass
class TextGuideColumnModel:
    """Header configuration for a column in a text guide table.

    Attributes:
        header: Display label for the column header (e.g. '1', '2', '3', '4').
        color: Hex color string or name for the header background (e.g. '#D32F2F', '#F57C00', '#388E3C', '#1976D2').
    """

    header: str
    color: str


@dataclass
class TextGuideTableModel:
    """Data model for a pure text matrix guide table (e.g. Psychological Safety Metric guide).

    Displays a title spanning across the columns, row labels on the left,
    colored column headers, and pure text cells.

    Attributes:
        title: Table main title displayed across top (e.g. 'PSYCHOLOGICAL SAFETY METRIC').
        row_label_header: Optional header text for the row labels column (can be empty string '').
        columns: List of TextGuideColumnModel for the data columns.
        row_labels: List of row names (e.g. ['Motivation', 'Connected', 'Workload', 'Teamwork']).
        matrix: 2D list [row][col] of string text cells corresponding to row_labels x columns.
    """

    title: str
    row_label_header: str
    columns: List[TextGuideColumnModel]
    row_labels: List[str]
    matrix: List[List[str]]

    def __post_init__(self) -> None:
        if len(self.matrix) != len(self.row_labels):
            raise ValueError(
                f"TextGuideTableModel mismatch: row_labels ({len(self.row_labels)}) "
                f"must match matrix rows ({len(self.matrix)})."
            )
        for r, row_vals in enumerate(self.matrix):
            if len(row_vals) != len(self.columns):
                raise ValueError(
                    f"TextGuideTableModel row {r} length ({len(row_vals)}) "
                    f"does not match columns ({len(self.columns)})."
                )


@dataclass
class SafetyQuestionModel:
    """Data model for a single safety assessment question and answer dropdown.

    Attributes:
        prompt_text: The descriptive text or question (e.g.,
                     'Motivation: Disengaged/Lack of Motivation / Motivated/ Energised').
        options: List of string options to display in the dropdown menu.
        selected_option: The currently selected or default option (optional).
    """

    prompt_text: str
    options: List[str]
    selected_option: Optional[str] = None


@dataclass
class SafetyQuestionnaireModel:
    """Data model for a safety assessment questionnaire card.

    Attributes:
        title: Title of the questionnaire card (e.g., 'Psychological Safety Assessment Questionnaire').
        questions: List of SafetyQuestionModel items.
        already_filled: Boolean flag indicating if this questionnaire has already been submitted.
        completed_message: Message to display when already_filled is True.
    """

    title: str
    questions: List[SafetyQuestionModel] = field(default_factory=list)
    already_filled: bool = False
    completed_message: str = "Thank you! This safety assessment has already been filled and submitted for the current period."


@dataclass
class SafetySummaryTableModel:
    """Data model for the revamped Safety Table Dashboard (e.g. Week 5 summary).

    Attributes:
        period_title: Top header title spanning all columns (e.g., 'Week 5').
        headers: Column headers (e.g., ['# No responses', 'Motivation Average', ...]).
        values: Corresponding string or numeric values for the row.
        total_index: Column index to highlight as the Total column (orange header, green cell).
        target_threshold: Numeric threshold to determine if the total average meets target (green vs red).
    """

    period_title: str
    headers: List[str]
    values: List[str]
    total_index: int = 5
    target_threshold: float = 2.5


@dataclass
class ParetoLogEntryModel:
    """Single log entry for Pareto loss admin tracking.

    Attributes:
        date: Date of the logged incident (e.g. '07/02').
        category: Pareto loss category (e.g. 'Machine Breakdown').
        comment: Description or root cause of the loss.
        inputs: Planned or target input value (e.g. '500 units' or '8.0 hrs').
        outputs: Actual output achieved (e.g. '420 units' or '6.5 hrs').
    """

    date: str
    category: str
    comment: str
    inputs: str
    outputs: str


@dataclass
class ParetoLogTableModel:
    """Data model for Pareto Table Admin (Incident & Loss Log with Inputs/Outputs).

    Attributes:
        title: Table title (e.g. 'Pareto Loss Admin Log').
        principal: Responsible person / admin reviewer.
        entries: List of ParetoLogEntryModel items.
    """

    title: str
    principal: str
    entries: List[ParetoLogEntryModel] = field(default_factory=list)



