import sys
from PyQt5.QtWidgets import QApplication
from services.graph_contract_validator import GraphContractValidator
from components.charts.contract_graph_harness import create_graph_widget_from_data, FirstTimeYieldGaugeWidget, ContractBarChartWidget

def test_offline_ci_and_pure_ui():
    print("-- Step 1: Offline CI Docker Build Gate Check (GraphContractValidator) --")
    validator = GraphContractValidator()
    print("Loaded offline graph contracts:", list(validator.contracts.keys()))

    # Verify sample FTY record passes CI
    valid_fty = [{"fty_percentage": 94.5}]
    is_valid, errors = validator.validate_graph_data("first_time_yield_gauge", valid_fty)
    assert is_valid, f"Expected valid FTY, got errors: {errors}"
    print("[PASS] FTY Gauge sample passed offline CI contract validation!")

    # Verify bad data is trapped during offline CI build gate before Docker build
    invalid_tickets = [
        {"day_label": "Mon", "tickets_merged": -5},
        {"day_label": "Tue"}
    ]
    is_valid, errors = validator.validate_graph_data("tickets_per_day_chart", invalid_tickets)
    assert not is_valid, "Expected validation failure offline for invalid_tickets"
    print("[PASS] Offline CI gate trapped contract violations before container build:")
    for err in errors:
        print("   -> [CI ERROR TRAPPED]", err)

    print("\n-- Step 2: Presentation Layer / Pure Qt Direct Rendering (No Runtime Validation Overhead) --")
    app = QApplication(sys.argv)

    # UI trusts valid database/model data and instantiates pure Qt widgets immediately
    valid_burndown_data = [
        {"date": "2026-07-01", "remaining_points": 120.0, "ideal_points": 120.0},
        {"date": "2026-07-02", "remaining_points": 90.0, "ideal_points": 100.0},
        {"date": "2026-07-03", "remaining_points": 45.0, "ideal_points": 60.0}
    ]
    
    widget_burndown = create_graph_widget_from_data("burndown_curve", valid_burndown_data)
    assert isinstance(widget_burndown, ContractBarChartWidget)
    print("[PASS] Direct instantiation of Burndown Curve widget completed without runtime validation check!")

    widget_gauge = create_graph_widget_from_data("first_time_yield_gauge", valid_fty)
    assert isinstance(widget_gauge, FirstTimeYieldGaugeWidget)
    print("[PASS] Direct instantiation of First Time Yield Gauge widget completed without runtime validation check!")

    print("\n[SUCCESS] OFFLINE CI GATE & PURE DIRECT QT GUI RENDERING VERIFIED AND WORKING PERFECTLY!")

if __name__ == "__main__":
    test_offline_ci_and_pure_ui()
