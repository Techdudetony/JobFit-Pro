# services/theme_manager.py
"""
Theme Manager
-------------

Handles light/dark mode switching and theme persistence.

v2 CHANGES:
- Supports two QSS files: app_dark.qss and app_light.qss
- Reads/writes to %APPDATA%/JobFitPro/config.json (merges with existing keys)
- Falls back to local theme_preference.json if AppData is unavailable
- PyInstaller-safe path resolution via _get_base_dir()
- is_dark_mode() / is_light_mode() convenience helpers
- get_theme_name() returns human-readable label for menu display
"""

import os
import sys
import json

from PyQt6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# AppData config path (Windows)
# ---------------------------------------------------------------------------
_APPDATA       = os.getenv("APPDATA", "")
_APP_CONFIG_DIR  = os.path.join(_APPDATA, "JobFitPro") if _APPDATA else ""
_APP_CONFIG_FILE = os.path.join(_APP_CONFIG_DIR, "config.json") if _APP_CONFIG_DIR else ""

# Local fallback
_LOCAL_THEME_FILE = "theme_preference.json"


def _get_base_dir() -> str:
    """
    Returns the root directory that contains the app/ folder.
    Works in both normal Python and PyInstaller .exe builds.
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ThemeManager:

    DARK  = "dark"
    LIGHT = "light"

    def __init__(self, app: QApplication):
        self.app = app
        self.current_theme = self.load_preference()

        base = _get_base_dir()
        self.styles_dir = os.path.join(base, "app", "styles")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def load_preference(self) -> str:
        """
        Load saved theme preference.
        Priority: %APPDATA%/JobFitPro/config.json → local file → 'dark'
        """
        # 1. AppData config
        if _APP_CONFIG_FILE and os.path.exists(_APP_CONFIG_FILE):
            try:
                with open(_APP_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    theme = data.get("theme")
                    if theme in (self.DARK, self.LIGHT):
                        return theme
            except Exception as e:
                print(f"[THEME] Could not read AppData config: {e}")

        # 2. Local fallback
        if os.path.exists(_LOCAL_THEME_FILE):
            try:
                with open(_LOCAL_THEME_FILE, "r") as f:
                    data = json.load(f)
                    theme = data.get("theme", self.DARK)
                    if theme in (self.DARK, self.LIGHT):
                        return theme
            except Exception as e:
                print(f"[THEME] Could not read local theme file: {e}")

        return self.DARK

    def save_preference(self, theme: str):
        """
        Save theme to %APPDATA%/JobFitPro/config.json (merging with existing
        keys) and also to local theme_preference.json as a backup.
        """
        # AppData config — merge, don't overwrite other keys
        if _APP_CONFIG_FILE:
            try:
                os.makedirs(_APP_CONFIG_DIR, exist_ok=True)
                data = {}
                if os.path.exists(_APP_CONFIG_FILE):
                    with open(_APP_CONFIG_FILE, "r") as f:
                        data = json.load(f)
                data["theme"] = theme
                with open(_APP_CONFIG_FILE, "w") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"[THEME] Could not write AppData config: {e}")

        # Always write local backup
        try:
            with open(_LOCAL_THEME_FILE, "w") as f:
                json.dump({"theme": theme}, f)
        except Exception as e:
            print(f"[THEME] Could not write local theme file: {e}")

        print(f"[THEME] Saved preference: {theme}")

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------
    def apply_theme(self, theme: str) -> bool:
        """
        Load and apply the QSS stylesheet for the given theme.
        Returns True on success, False on failure.
        """
        qss_file = "app.qss" if theme == self.DARK else "app_light.qss"
        qss_path = os.path.join(self.styles_dir, qss_file)

        if not os.path.exists(qss_path):
            print(f"[THEME] QSS file not found: {qss_path}")
            return False

        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()

            self.app.setStyleSheet(stylesheet)
            self.current_theme = theme
            self.save_preference(theme)
            print(f"[THEME] Applied {theme} mode")
            return True

        except Exception as e:
            print(f"[THEME] Failed to apply {theme} theme: {e}")
            return False

    def toggle_theme(self) -> bool:
        """Toggle between dark and light. Returns True on success."""
        new_theme = self.LIGHT if self.current_theme == self.DARK else self.DARK
        return self.apply_theme(new_theme)

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def is_dark_mode(self) -> bool:
        return self.current_theme == self.DARK

    def is_light_mode(self) -> bool:
        return self.current_theme == self.LIGHT

    def get_theme_name(self) -> str:
        """Human-readable label — handy for menu items."""
        return "Dark Mode" if self.is_dark_mode() else "Light Mode"


# ---------------------------------------------------------------------------
# Singleton — assigned in main.py, imported everywhere else
# ---------------------------------------------------------------------------
theme_manager: ThemeManager | None = None