# app/ui/tabs/tab_settings.py
"""
Settings Tab — JobFit Pro
--------------------------

User-configurable preferences:
- OpenAI API Key (masked input with show/hide)
- Model selector
- Theme toggle
- Default tailoring preferences
"""

import os
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QCheckBox, QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "assets", "icons",
)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".jobfitpro", "config.json")


def _load_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_config(data: dict):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[SETTINGS] Failed to save config: {e}")


class SettingsTab(QWidget):
    def __init__(self, settings_panel=None, parent=None):
        super().__init__(parent)
        self._settings_panel = settings_panel  # direct ref to TailorTab.settingsPanel
        self._build_ui()
        self._load_current_values()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        title = QLabel("Settings")
        title.setProperty("panelTitle", True)
        root.addWidget(title)

        # ── API Configuration ─────────────────────────────────────
        api_group = QGroupBox("API Configuration")
        api_form  = QFormLayout(api_group)
        api_form.setSpacing(12)

        # API Key row
        key_row = QHBoxLayout()
        self.input_api_key = QLineEdit()
        self.input_api_key.setPlaceholderText("sk-...")
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setObjectName("authField")

        self.btn_toggle_key = QPushButton()
        not_vis = os.path.join(ICONS_DIR, "not_visible.svg")
        self.btn_toggle_key.setIcon(QIcon(not_vis))
        self.btn_toggle_key.setFixedSize(32, 32)
        self.btn_toggle_key.setProperty("panelButton", True)
        self.btn_toggle_key.clicked.connect(self._toggle_api_key_visibility)

        key_row.addWidget(self.input_api_key)
        key_row.addWidget(self.btn_toggle_key)
        api_form.addRow("OpenAI API Key:", key_row)

        # Model selector
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ])
        api_form.addRow("Model:", self.combo_model)

        self.btn_save_api = QPushButton("Save API Settings")
        self.btn_save_api.clicked.connect(self._save_api_settings)
        api_form.addRow("", self.btn_save_api)

        root.addWidget(api_group)

        # ── Appearance ────────────────────────────────────────────
        appear_group = QGroupBox("Appearance")
        appear_form  = QFormLayout(appear_group)
        appear_form.setSpacing(12)

        self.btn_toggle_theme = QPushButton("Switch to Light Mode")
        self.btn_toggle_theme.clicked.connect(self._toggle_theme)
        appear_form.addRow("Theme:", self.btn_toggle_theme)

        root.addWidget(appear_group)

        # ── Default Tailoring Preferences ────────────────────────
        pref_group = QGroupBox("Default Tailoring Preferences")
        pref_form  = QFormLayout(pref_group)
        pref_form.setSpacing(12)

        self.chk_default_keywords  = QCheckBox("Emphasize job keywords")
        self.chk_default_ats       = QCheckBox("ATS-friendly formatting")
        self.chk_default_ats.setChecked(True)
        self.chk_default_keep_len  = QCheckBox("Keep similar length")
        self.chk_default_one_page  = QCheckBox("Limit to 1 page")

        pref_form.addRow(self.chk_default_keywords)
        pref_form.addRow(self.chk_default_ats)
        pref_form.addRow(self.chk_default_keep_len)
        pref_form.addRow(self.chk_default_one_page)

        self.btn_save_prefs = QPushButton("Save Preferences")
        self.btn_save_prefs.clicked.connect(self._save_preferences)
        pref_form.addRow("", self.btn_save_prefs)

        root.addWidget(pref_group)

        root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    # ----------------------------------------------------------
    def _toggle_api_key_visibility(self):
        hidden = self.input_api_key.echoMode() == QLineEdit.EchoMode.Password
        self.input_api_key.setEchoMode(
            QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password
        )
        icon_name = "visible.svg" if hidden else "not_visible.svg"
        self.btn_toggle_key.setIcon(
            QIcon(os.path.join(ICONS_DIR, icon_name))
        )

    def _toggle_theme(self):
        try:
            import services.theme_manager as tm
            if tm.theme_manager:
                tm.theme_manager.toggle_theme()
                is_dark = tm.theme_manager.is_dark_mode()
                self.btn_toggle_theme.setText(
                    "Switch to Light Mode" if is_dark else "Switch to Dark Mode"
                )
        except Exception as e:
            print(f"[SETTINGS] Theme toggle failed: {e}")

    def _save_api_settings(self):
        """Write API key + model to .env file."""
        from PyQt6.QtWidgets import QMessageBox
        key   = self.input_api_key.text().strip()
        model = self.combo_model.currentText()

        env_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "..", ".env"
        )
        env_path = os.path.normpath(env_path)

        try:
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()

            def set_env(lines, key_name, value):
                for i, line in enumerate(lines):
                    if line.startswith(f"{key_name}="):
                        lines[i] = f"{key_name}={value}\n"
                        return lines
                lines.append(f"{key_name}={value}\n")
                return lines

            if key:
                lines = set_env(lines, "OPENAI_API_KEY", key)
            lines = set_env(lines, "OPENAI_MODEL_NAME", model)

            with open(env_path, "w") as f:
                f.writelines(lines)

            QMessageBox.information(
                self, "Saved",
                "API settings saved.\nRestart the app for changes to take effect."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save settings:\n{e}")

    def _save_preferences(self):
        from PyQt6.QtWidgets import QMessageBox
        import json

        prefs = {
            "focus_keywords": self.chk_default_keywords.isChecked(),
            "ats_friendly":   self.chk_default_ats.isChecked(),
            "keep_length":    self.chk_default_keep_len.isChecked(),
            "limit_one":      self.chk_default_one_page.isChecked(),
        }

        cfg = _load_config()
        cfg["default_prefs"] = prefs
        _save_config(cfg)

        # Apply to Tailor tab's settingsPanel immediately via direct reference
        if self._settings_panel:
            try:
                self._settings_panel.chk_focus_keywords.setChecked(prefs["focus_keywords"])
                self._settings_panel.chk_ats_friendly.setChecked(prefs["ats_friendly"])
                self._settings_panel.chk_keep_length.setChecked(prefs["keep_length"])
                self._settings_panel.chk_limit_one.setChecked(prefs["limit_one"])
            except Exception as e:
                print(f"[SETTINGS] Failed to apply prefs to tailor tab: {e}")

        QMessageBox.information(self, "Saved", "Default preferences saved and applied.")

    def _load_current_values(self):
        """Pre-fill fields with current .env values."""
        try:
            from dotenv import dotenv_values
            env_path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "..", ".env"
            ))
            vals = dotenv_values(env_path)

            key = vals.get("OPENAI_API_KEY", "")
            if key:
                self.input_api_key.setText(key)

            model = vals.get("OPENAI_MODEL_NAME", "gpt-4.1")
            idx   = self.combo_model.findText(model)
            if idx >= 0:
                self.combo_model.setCurrentIndex(idx)
        except Exception:
            pass

        # Sync theme button label
        try:
            import services.theme_manager as tm
            if tm.theme_manager:
                is_dark = tm.theme_manager.is_dark_mode()
                self.btn_toggle_theme.setText(
                    "Switch to Light Mode" if is_dark else "Switch to Dark Mode"
                )
        except Exception:
            pass

        # Load saved default preferences
        prefs = _load_config().get("default_prefs", {})
        if prefs:
            self.chk_default_keywords.setChecked(prefs.get("focus_keywords", False))
            self.chk_default_ats.setChecked(prefs.get("ats_friendly", True))
            self.chk_default_keep_len.setChecked(prefs.get("keep_length", False))
            self.chk_default_one_page.setChecked(prefs.get("limit_one", False))