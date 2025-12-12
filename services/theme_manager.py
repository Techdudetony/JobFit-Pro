"""
Theme Manager
-------------

Handles light/dark mode switching and theme persistence.
"""

import os
import json
from PyQt6.QtWidgets import QApplication

THEME_CONFIG_FILE = "theme_preference.json"


class ThemeManager:
    def __init__(self, app: QApplication):
        self.app = app
        self.current_theme = self.load_preference()
        # Get the project root directory (where main.py is located)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.styles_dir = os.path.join(project_root, "app", "styles")

    def load_preference(self) -> str:
        """Load saved theme preference (defaults to 'dark')."""
        try:
            if os.path.exists(THEME_CONFIG_FILE):
                with open(THEME_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("theme", "dark")
        except Exception as e:
            print(f"[THEME] Failed to load preference: {e}")
        return "dark"

    def save_preference(self, theme: str):
        """Save theme preference to file."""
        try:
            with open(THEME_CONFIG_FILE, "w") as f:
                json.dump({"theme": theme}, f)
            print(f"[THEME] Saved preference: {theme}")
        except Exception as e:
            print(f"[THEME] Failed to save preference: {e}")

    def apply_theme(self, theme: str):
        """Apply the specified theme stylesheet."""
        try:
            qss_file = "app_dark.qss" if theme == "dark" else "app_light.qss"
            qss_path = os.path.join(self.styles_dir, qss_file)

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

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        return self.apply_theme(new_theme)

    def is_dark_mode(self) -> bool:
        """Check if current theme is dark mode."""
        return self.current_theme == "dark"


# Singleton instance (initialized in main.py)
theme_manager = None
