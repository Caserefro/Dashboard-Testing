import json
import os
import re
from typing import List, Dict, Any, Tuple, Optional

class GraphContractValidator:
    """
    Component B: CI Contract Validator for Dashboard Graphs.
    Loads config/ui_graph_contracts.json and enforces strict schema compliance on incoming data.
    """
    def __init__(self, contract_file_path: Optional[str] = None):
        if contract_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            contract_file_path = os.path.join(base_dir, "config", "ui_graph_contracts.json")
        self.contract_file_path = contract_file_path
        self.contracts = self._load_contracts()

    def _load_contracts(self) -> Dict[str, Any]:
        if not os.path.exists(self.contract_file_path):
            raise FileNotFoundError(f"Contract file not found at: {self.contract_file_path}")
        with open(self.contract_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("graphs", {})

    def get_graph_contract(self, graph_key: str) -> Optional[Dict[str, Any]]:
        return self.contracts.get(graph_key)

    def validate_graph_data(self, graph_key: str, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validates a list of data rows/records against the contract defined for graph_key.
        Returns (is_valid, list_of_error_messages).
        """
        errors = []
        contract = self.get_graph_contract(graph_key)
        if not contract:
            return False, [f"Contract not defined for graph_key: '{graph_key}' in schema."]

        if not isinstance(data, list):
            return False, ["Input data must be a list of records/objects."]

        if len(data) == 0:
            return False, [f"Input data for '{graph_key}' is empty. At least one data record is required."]

        required_fields = contract.get("required_fields", [])

        for row_idx, row in enumerate(data):
            if not isinstance(row, dict):
                errors.append(f"Row {row_idx}: must be a JSON object/dictionary.")
                continue

            for field_spec in required_fields:
                field_name = field_spec.get("name")
                expected_type = field_spec.get("type")
                min_val = field_spec.get("min_value")
                max_val = field_spec.get("max_value")

                if field_name not in row or row[field_name] is None:
                    errors.append(f"Row {row_idx}: missing required field '{field_name}'.")
                    continue

                val = row[field_name]

                # Check types
                if expected_type == "float":
                    if not isinstance(val, (int, float)):
                        errors.append(f"Row {row_idx} field '{field_name}': expected float, got {type(val).__name__}.")
                        continue
                    val = float(val)
                elif expected_type == "integer":
                    if not isinstance(val, int) or isinstance(val, bool):
                        errors.append(f"Row {row_idx} field '{field_name}': expected integer, got {type(val).__name__}.")
                        continue
                elif expected_type == "string":
                    if not isinstance(val, str):
                        errors.append(f"Row {row_idx} field '{field_name}': expected string, got {type(val).__name__}.")
                        continue
                elif expected_type == "string_iso8601":
                    if not isinstance(val, str):
                        errors.append(f"Row {row_idx} field '{field_name}': expected string_iso8601, got {type(val).__name__}.")
                        continue
                    # Simple ISO-8601 regex check (e.g., YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
                    if not re.match(r"^\d{4}-\d{2}-\d{2}", val):
                        errors.append(f"Row {row_idx} field '{field_name}': '{val}' is not a valid ISO-8601 date string.")
                        continue

                # Check min/max bounds if numeric
                if isinstance(val, (int, float)):
                    if min_val is not None and val < min_val:
                        errors.append(f"Row {row_idx} field '{field_name}': value {val} is below minimum allowed value {min_val}.")
                    if max_val is not None and val > max_val:
                        errors.append(f"Row {row_idx} field '{field_name}': value {val} exceeds maximum allowed value {max_val}.")

        return len(errors) == 0, errors

if __name__ == "__main__":
    # Test execution for CI / command-line validation
    validator = GraphContractValidator()
    print("SUCCESS: GraphContractValidator initialized. Loaded contracts for:", list(validator.contracts.keys()))
