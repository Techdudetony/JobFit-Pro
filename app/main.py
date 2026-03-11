import sys
import os
from PyQt6.QtWidgets import QApplication
from app.window_main import MainWindow
from services.theme_manager import ThemeManager
import services.theme_manager as tm_module


def main():
    app = QApplication(sys.argv)

    # Initialize theme manager — loads saved preference and applies QSS
    tm_module.theme_manager = ThemeManager(app)
    tm_module.theme_manager.apply_theme(tm_module.theme_manager.current_theme)

    # Create window (handles auth internally)
    print("Creating MainWindow...")
    window = MainWindow()

    if window.auth_ok:
        window.show()
    else:
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()