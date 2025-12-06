"""
Application entry point.
"""

import sys
from PyQt6.QtWidgets import QApplication
from app.window_main import MainWindow
from app.ui.auth_modal import AuthModal
from services.auth_manager import AuthManager


def main():
    app = QApplication(sys.argv)

    # Load stylesheet if exists
    try:
        with open("app/styles/app.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except:
        pass

    auth = AuthManager()

    # -----------------------------
    # AUTH REQUIRED BEFORE UI OPENS
    # -----------------------------
    if not auth.user:  # No session → show login modal
        modal = AuthModal()
        result = modal.exec()

        if result != modal.Accepted:
            print("User exited before signing in. Closing app.")
            sys.exit(0)

    # If we reach here → user is authenticated
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
