"""
repositories.mock.mock_table_repository
=======================================
Mock repository for table data (Pareto Loss Table, Safety Assessment Table).

Implements the duck-typed repository contract:
    * get_data(**filters) -> Optional[Any]
    * save_data(data) -> bool
"""

import random
from typing import Optional, Any, List
from models.table_models import ParetoTableModel, SafetyTableModel, SafetyFieldModel


class MockTableRepository:
    """Mock repository providing simulated Pareto and Safety table models."""

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}

    def get_data(self, **filters: Any) -> Optional[Any]:
        """Retrieve table model based on table_type filter.

        Parameters
        ----------
        table_type : str
            One of 'pareto', 'safety'.
        """
        table_type = filters.get("table_type", "pareto")

        if table_type in self._storage:
            return self._storage[table_type]

        if table_type == "pareto":
            model = self._generate_pareto_table()
        elif table_type == "safety":
            model = self._generate_safety_table()
        else:
            return None

        self._storage[table_type] = model
        return model

    def save_data(self, data: Any) -> bool:
        """Persist table model to in-memory storage."""
        if isinstance(data, ParetoTableModel):
            self._storage["pareto"] = data
            return True
        elif isinstance(data, SafetyTableModel):
            self._storage["safety"] = data
            return True
        return False

    def _generate_pareto_table(self) -> ParetoTableModel:
        categories = [
            "Support", "Mg availability", "Mg performance",
            "Task Planning", "Work Standards", "Training Needs",
            "Input Delays", "Input Quality",
        ]
        n_weeks = random.randint(5, 9)
        columns = [str(w) for w in range(13, 13 + n_weeks)]
        values = [[random.randint(0, 12) for _ in range(n_weeks)] for _ in categories]
        averages = [round(sum(row) / len(row), 1) for row in values]
        return ParetoTableModel(
            title="Where Pareto",
            categories=categories,
            columns=columns,
            values=values,
            averages=averages,
        )

    def _generate_safety_table(self) -> SafetyTableModel:
        safety_cats = ["Ergonomic", "Chemical", "Physical", "Biological", "Psychosocial"]
        field_names = [
            "Workstation posture", "Chemical storage", "Noise levels",
            "PPE compliance", "Work-life balance", "Emergency exits",
            "Fire extinguishers", "First aid kits",
        ]
        fields = []
        for name in field_names:
            cat = random.choice(safety_cats)
            val = random.choice(["Compliant", "Non-Compliant", "Pending Review", "N/A"])
            comment = random.choice(["", "Needs follow-up", "Resolved", "Scheduled for review"])
            fields.append(SafetyFieldModel(
                field_name=name, field_value=val,
                category=cat, comment=comment,
            ))
        return SafetyTableModel(
            title="Safety Assessment",
            principal="Safety Officer - J. Martinez",
            categories=safety_cats,
            fields=fields,
        )
