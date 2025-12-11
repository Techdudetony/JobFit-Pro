"""
main.py
-------

Application entry point.

Responsibilities:
- Create QApplication
- Load global stylesheet
- Enforce authentication before launching main window
- Start MainWindow only after successful login
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog

from services.auth_manager import auth
from app.ui.auth_modal import AuthModal
from app.window_main import MainWindow


# ==================================================================
# Load Stylesheet
# ==================================================================
def load_styles(app: QApplication):
    """Load the global QSS stylesheet for JobFit Pro."""
    try:
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "app.qss")
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        print("Stylesheet loaded successfully.")
    except Exception as e:
        print("Failed to load QSS stylesheet:", e)


# ==================================================================
# Main Entry
# ==================================================================
def main():
    app = QApplication(sys.argv)

    # Global stylesheet
    load_styles(app)

    # --------------------------------------------------------------
    # Authentication Gate
    # --------------------------------------------------------------
    if auth.get_user() is None:
        modal = AuthModal()
        result = modal.exec()

        # User closed modal or failed authentication
        if result != QDialog.DialogCode.Accepted:
            print("Authentication failed or canceled — closing app.")
            sys.exit(0)

    # --------------------------------------------------------------
    # Launch Main Window
    # --------------------------------------------------------------
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
