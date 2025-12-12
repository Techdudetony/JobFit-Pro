"""
main.py
-------

Application entry point.

Responsibilities:
- Create QApplication
- Load global stylesheet with theme support
- Enforce authentication before launching main window
- Start MainWindow only after successful login
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog

from services.auth_manager import auth
from services.theme_manager import ThemeManager, theme_manager as tm
from app.ui.auth_modal import AuthModal
from app.window_main import MainWindow


# ==================================================================
# Main Entry
# ==================================================================
def main():
    app = QApplication(sys.argv)

    # Initialize theme manager
    global theme_manager
    from services import theme_manager as tm_module

    tm_module.theme_manager = ThemeManager(app)

    # Apply saved theme preference
    saved_theme = tm_module.theme_manager.load_preference()
    tm_module.theme_manager.apply_theme(saved_theme)

    # --------------------------------------------------------------
    # Authentication Gate
    # --------------------------------------------------------------
    # Try to restore saved session first
    if auth.has_saved_session():
        print("[AUTH] Found saved session, attempting auto-login...")
        user, error = auth.load_saved_session()
        if user and not error:
            print(f"[AUTH] Auto-login successful for {user.email}")
            # Skip modal, proceed directly to main window
        else:
            print(f"[AUTH] Auto-login failed: {error}")
            # Show modal for manual login
            modal = AuthModal()
            result = modal.exec()
            if result != QDialog.DialogCode.Accepted:
                print("Authentication failed or canceled – closing app.")
                sys.exit(0)
    elif auth.get_user() is None:
        # No saved session, show login modal
        modal = AuthModal()
        result = modal.exec()
        if result != QDialog.DialogCode.Accepted:
            print("Authentication failed or canceled – closing app.")
            sys.exit(0)

    # --------------------------------------------------------------
    # Launch Main Window
    # --------------------------------------------------------------
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
