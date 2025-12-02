"""
Application entry point.
"""

import sys
from PyQt6.QtWidgets import QApplication
from app.window_main import MainWindow


def main():
    app = QApplication(sys.argv)

    # Try to load global stylesheet
    try:
        with open("app/styles/app.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        # Failing to load the stylesheet should not crash the app
        pass

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
