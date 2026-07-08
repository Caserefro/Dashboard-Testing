"""
WOR Dashboard — Main Root Entry Point
=====================================

A convenient root wrapper script that launches the unified master
dashboard application from the structured `apps/` package.

Usage:
    python dashboard.py
"""

import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from apps.dashboard_app import WORDashboardApp


def main() -> None:
    """Launch the unified WOR Dashboard application."""
    app = QApplication(sys.argv)
    window = WORDashboardApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR: Failed to launch WOR Dashboard.\nDetails: {e}")
        traceback.print_exc()
        sys.exit(1)
