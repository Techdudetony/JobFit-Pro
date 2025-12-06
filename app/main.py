# app/main.py
"""
Application entry point for JobFit Pro (desktop).

Usage:
    python -m app.main
"""

import sys
from PyQt6.QtWidgets import QApplication
from app.window_main import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    print("Creating MainWindow...")
    window = MainWindow()
    print("MainWindow created, auth_ok:", getattr(window, "auth_ok", False))

    # If authentication failed or was cancelled, just exit cleanly
    if not getattr(window, "auth_ok", False):
        print("No authenticated user; application will exit.")
        sys.exit(0)

    # Otherwise, show the main window
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
