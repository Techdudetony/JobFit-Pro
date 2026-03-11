"""
main.py
-------

Application entry point.

Responsibilities:
- Create QApplication
- Initialize ThemeManager and apply saved theme
- Check grace period (60s auto-login) and Remember Me before showing modal
- Start MainWindow only after successful authentication
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog

from services.auth_manager import auth
from services.theme_manager import ThemeManager
import services.theme_manager as tm_module
from app.ui.auth_modal import AuthModal
from app.window_main import MainWindow


def main():
    app = QApplication(sys.argv)

    # ------------------------------------------------------------------
    # Initialize ThemeManager + apply saved preference
    # ------------------------------------------------------------------
    tm_module.theme_manager = ThemeManager(app)
    tm_module.theme_manager.apply_theme(tm_module.theme_manager.load_preference())

    # ------------------------------------------------------------------
    # Authentication Gate — 3 possible paths:
    #
    #   1. Within grace period (closed < 60s ago) + valid session → skip modal
    #   2. Remember Me session exists + still valid → skip modal
    #   3. No valid session → show AuthModal
    # ------------------------------------------------------------------
    authenticated = False

    # PATH 1: Grace period check (takes priority — fastest path)
    if auth.within_grace_period() and auth.has_saved_session():
        print("[AUTH] Within grace period — attempting silent restore...")
        user, error = auth.load_saved_session()
        if user and not error:
            print(f"[AUTH] Grace period login OK for {user.email}")
            authenticated = True
        else:
            print(f"[AUTH] Grace period restore failed: {error}")
            auth.clear_grace_period()

    # PATH 2: Full Remember Me session
    if not authenticated and auth.has_saved_session() and auth.is_remember_me_session():
        print("[AUTH] Remember Me session found — attempting restore...")
        user, error = auth.load_saved_session()
        if user and not error:
            print(f"[AUTH] Remember Me login OK for {user.email}")
            authenticated = True
        else:
            print(f"[AUTH] Remember Me restore failed: {error}")
            auth.clear_saved_session()

    # PATH 3: Show login modal
    if not authenticated:
        modal = AuthModal()
        result = modal.exec()
        if result != QDialog.DialogCode.Accepted:
            print("[AUTH] Login cancelled — exiting.")
            sys.exit(0)

    # ------------------------------------------------------------------
    # Launch Main Window
    # ------------------------------------------------------------------
    window = MainWindow()
    window.show()

    exit_code = app.exec()

    # ------------------------------------------------------------------
    # On close — stamp the time for grace period on next launch
    # Only stamp if user didn't explicitly sign out (user still set)
    # ------------------------------------------------------------------
    if auth.get_user() is not None:
        auth.stamp_close_time()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()