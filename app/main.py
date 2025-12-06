import sys
import os
from PyQt6.QtWidgets import QApplication
from app.window_main import MainWindow
from services.auth_manager import auth

def load_styles(app: QApplication):
    """Load global QSS styles."""
    try:
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "app.qss")
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        print("Stylesheet loaded successfully.")
    except Exception as e:
        print("Failed to load QSS stylesheet:", e)

def main():
    app = QApplication(sys.argv)

    # Load the global stylesheet
    load_styles(app)

    # Create window
    print("Creating MainWindow...")
    window = MainWindow()

    if auth.get_user():
        print("User authenticated — showing main window.")
        window.show()
    else:
        print("No session — showing auth modal instead.")
        window.show_auth_modal()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
