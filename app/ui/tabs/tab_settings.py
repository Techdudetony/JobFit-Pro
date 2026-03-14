# app/ui/tabs/tab_settings.py
"""
Settings Tab — JobFit Pro
--------------------------

User-configurable preferences:
- OpenAI API Key (masked input with show/hide)
- Model selector
- Theme toggle
- Default tailoring preferences
- Cloud sync (push all history / pull from cloud)
"""

import os
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QCheckBox, QSpacerItem, QSizePolicy,
    QMessageBox, QButtonGroup, QRadioButton, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from app.components.style_picker_widget import StylePickerWidget

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


class _ApiConnectionWorker(QThread):
    """Pings OpenAI in the background to verify the API key is valid."""
    result = pyqtSignal(bool, str)   # (ok, message)

    def run(self):
        try:
            import os
            from openai import OpenAI
            key = os.getenv("OPENAI_API_KEY", "")
            if not key:
                self.result.emit(False, "No API key found in environment")
                return
            client = OpenAI(api_key=key)
            client.models.list()   # lightweight call — just verifies auth
            self.result.emit(True, "API Connected  ✓")
        except Exception as e:
            msg = str(e)
            if "401" in msg or "Incorrect API key" in msg or "Authentication" in msg:
                self.result.emit(False, "Invalid API key")
            elif "connect" in msg.lower() or "network" in msg.lower():
                self.result.emit(False, "No internet connection")
            else:
                self.result.emit(False, f"Connection error")


class SettingsTab(QWidget):
    def __init__(self, settings_panel=None, parent=None):
        super().__init__(parent)
        self._settings_panel = settings_panel  # direct ref to TailorTab.settingsPanel
        self._build_ui()
        self._load_current_values()

    def _build_ui(self):
        # Outer layout holds just the scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        # Inner widget holds all the actual settings content
        inner = QWidget()
        inner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll.setWidget(inner)

        root = QVBoxLayout(inner)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        title = QLabel("Settings")
        title.setProperty("panelTitle", True)
        root.addWidget(title)

        # ── API Configuration ─────────────────────────────────────
        api_group = QGroupBox("API Configuration")
        api_form  = QFormLayout(api_group)
        api_form.setSpacing(12)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        self.lbl_api_dot = QLabel("●")
        self.lbl_api_dot.setFixedWidth(16)
        self.lbl_api_dot.setProperty("apiDot", "checking")

        self.lbl_api_status = QLabel("Checking connection...")
        self.lbl_api_status.setProperty("apiStatus", True)

        self.btn_api_recheck = QPushButton("Re-check")
        self.btn_api_recheck.setProperty("panelButton", True)
        self.btn_api_recheck.setFixedWidth(80)
        self.btn_api_recheck.clicked.connect(self._check_api_connection)

        status_row.addWidget(self.lbl_api_dot)
        status_row.addWidget(self.lbl_api_status)
        status_row.addStretch()
        status_row.addWidget(self.btn_api_recheck)
        api_form.addRow("Status:", status_row)

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

        self.btn_save_api = QPushButton("Save Model Preference")
        self.btn_save_api.clicked.connect(self._save_model_preference)
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


        # ── Cloud Sync ────────────────────────────────────────────
        sync_group = QGroupBox("Cloud Sync")
        sync_layout = QVBoxLayout(sync_group)
        sync_layout.setSpacing(10)

        # Status label
        self.lbl_sync_status = QLabel("Last synced: never")
        self.lbl_sync_status.setStyleSheet("color: #94A3B8; font-size: 9pt;")
        sync_layout.addWidget(self.lbl_sync_status)

        # Button row
        sync_btn_row = QHBoxLayout()

        self.btn_push_cloud = QPushButton("⬆  Push All to Cloud")
        self.btn_push_cloud.setToolTip("Upload all local tailoring history to Supabase")
        self.btn_push_cloud.clicked.connect(self._push_all_to_cloud)

        self.btn_pull_cloud = QPushButton("⬇  Pull from Cloud")
        self.btn_pull_cloud.setToolTip("Download cloud history and merge with local history")
        self.btn_pull_cloud.setProperty("panelButton", True)
        self.btn_pull_cloud.clicked.connect(self._pull_from_cloud)

        sync_btn_row.addWidget(self.btn_push_cloud)
        sync_btn_row.addWidget(self.btn_pull_cloud)
        sync_layout.addLayout(sync_btn_row)

        root.addWidget(sync_group)


        # ── Resume Style ──────────────────────────────────────────
        style_group = QGroupBox("Default Resume Style")
        style_layout = QVBoxLayout(style_group)
        style_layout.setSpacing(10)

        style_desc = QLabel(
            "Choose the default visual style applied when exporting tailored resumes."
        )
        style_desc.setWordWrap(True)
        style_desc.setProperty("subtitleLabel", True)
        style_layout.addWidget(style_desc)

        self.style_picker = StylePickerWidget(self)
        self.style_picker.styleSelected.connect(self._on_style_selected)
        style_layout.addWidget(self.style_picker)

        self.btn_save_style = QPushButton("Save Style Preference")
        self.btn_save_style.clicked.connect(self._save_style)
        style_layout.addWidget(self.btn_save_style)

        root.addWidget(style_group)

        root.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    # ----------------------------------------------------------
    def _set_api_status(self, state: str, message: str):
        """Update status dot and label. state: 'checking'|'connected'|'error'"""
        self.lbl_api_dot.setProperty("apiDot", state)
        self.lbl_api_status.setText(message)
        self.lbl_api_dot.style().unpolish(self.lbl_api_dot)
        self.lbl_api_dot.style().polish(self.lbl_api_dot)

    def _check_api_connection(self):
        """Fire a background ping to verify the OpenAI key works."""
        self._set_api_status("checking", "Checking connection...")
        self.btn_api_recheck.setEnabled(False)
        self._api_checker = _ApiConnectionWorker()
        self._api_checker.result.connect(self._on_api_check_result)
        self._api_checker.start()

    def _on_api_check_result(self, ok: bool, message: str):
        self.btn_api_recheck.setEnabled(True)
        if ok:
            self._set_api_status("connected", message)
        else:
            self._set_api_status("error", message)

    def _save_model_preference(self):
        """Save selected model to .env without touching the API key."""
        model = self.combo_model.currentText()
        env_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "..", ".env"
        ))
        try:
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("OPENAI_MODEL_NAME="):
                    lines[i] = f"OPENAI_MODEL_NAME={model}\n"
                    updated = True
                    break
            if not updated:
                lines.append(f"OPENAI_MODEL_NAME={model}\n")
            with open(env_path, "w") as f:
                f.writelines(lines)
            QMessageBox.information(
                self, "Saved",
                f"Model preference saved: {model}\nRestart the app for changes to take effect."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save model preference:\n{e}")

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

        # Push updated prefs to Supabase
        try:
            from services.sync_manager import sync_manager
            import services.theme_manager as tm
            theme = "dark"
            if tm.theme_manager:
                theme = "dark" if tm.theme_manager.is_dark_mode() else "light"
            sync_manager.push_preferences(theme, prefs)
        except Exception as e:
            print(f"[SETTINGS] Failed to push prefs to cloud: {e}")

        QMessageBox.information(self, "Saved", "Default preferences saved and applied.")

    def _load_current_values(self):
        """Load saved preferences into UI controls."""
        try:
            from dotenv import dotenv_values
            env_path = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "..", "..", ".env"
            ))
            vals = dotenv_values(env_path)
            model = vals.get("OPENAI_MODEL_NAME", "gpt-4.1")
            idx   = self.combo_model.findText(model)
            if idx >= 0:
                self.combo_model.setCurrentIndex(idx)
        except Exception:
            pass

        # Kick off API connection check after short delay
        QTimer.singleShot(300, self._check_api_connection)

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

        # Load last synced timestamp
        last_synced = _load_config().get("last_synced", "never")
        self.lbl_sync_status.setText(f"Last synced: {last_synced}")

        # Load saved resume style
        saved_style = _load_config().get("resume_style", "prestige")
        self.style_picker.set_selected(saved_style)

    # ----------------------------------------------------------
    # Sync: Push ALL local history to Supabase
    # ----------------------------------------------------------
    def _push_all_to_cloud(self):
        from services.sync_manager import sync_manager
        from services.auth_manager import auth

        if not auth.get_user():
            QMessageBox.warning(self, "Not Signed In",
                                "You must be signed in to sync.")
            return

        history_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "data", "tailoring_history.json"
        ))

        try:
            if not os.path.exists(history_path):
                QMessageBox.information(self, "Nothing to Sync",
                                        "No local history found.")
                return
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read history:\n{e}")
            return

        if not history:
            QMessageBox.information(self, "Nothing to Sync",
                                    "Your local history is empty.")
            return

        self.btn_push_cloud.setEnabled(False)
        self.btn_pull_cloud.setEnabled(False)
        self.btn_push_cloud.setText("Pushing…")

        self._push_total  = len(history)
        self._push_done   = 0
        self._push_errors = 0

        def _on_one_done(_id=""):
            self._push_done += 1
            self._check_push_complete()

        def _on_one_error(msg):
            self._push_done  += 1
            self._push_errors += 1
            print(f"[SYNC] push error: {msg}")
            self._check_push_complete()

        for entry in history:
            sync_manager.push_history_entry(entry,
                                            on_done=_on_one_done,
                                            on_error=_on_one_error)

    def _check_push_complete(self):
        if self._push_done < self._push_total:
            return
        self.btn_push_cloud.setEnabled(True)
        self.btn_pull_cloud.setEnabled(True)
        self.btn_push_cloud.setText("⬆  Push All to Cloud")

        if self._push_errors == 0:
            self._set_synced_now()
            QMessageBox.information(
                self, "Sync Complete",
                f"✅ {self._push_total} "
                f"entr{'y' if self._push_total == 1 else 'ies'} pushed successfully."
            )
        else:
            QMessageBox.warning(
                self, "Sync Partial",
                f"{self._push_total - self._push_errors} pushed, "
                f"{self._push_errors} failed. Check console for details."
            )

    # ----------------------------------------------------------
    # Sync: Pull from Cloud + merge with local
    # ----------------------------------------------------------
    def _pull_from_cloud(self):
        from services.sync_manager import sync_manager
        from services.auth_manager import auth

        if not auth.get_user():
            QMessageBox.warning(self, "Not Signed In",
                                "You must be signed in to sync.")
            return

        self.btn_push_cloud.setEnabled(False)
        self.btn_pull_cloud.setEnabled(False)
        self.btn_pull_cloud.setText("Pulling…")

        history_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "data", "tailoring_history.json"
        ))

        try:
            local = json.load(open(history_path, "r", encoding="utf-8")) \
                if os.path.exists(history_path) else []
        except Exception:
            local = []

        def _on_pulled(merged: list):
            try:
                os.makedirs(os.path.dirname(history_path), exist_ok=True)
                with open(history_path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, indent=4)
            except Exception as e:
                print(f"[SYNC] Failed to write merged history: {e}")

            self.btn_pull_cloud.setEnabled(True)
            self.btn_push_cloud.setEnabled(True)
            self.btn_pull_cloud.setText("⬇  Pull from Cloud")
            self._set_synced_now()

            # Tell main window to refresh History tab
            try:
                win = self.window()
                if hasattr(win, "_refresh_history_tab"):
                    win._refresh_history_tab(merged)
            except Exception:
                pass

            QMessageBox.information(
                self, "Pull Complete",
                f"✅ {len(merged)} "
                f"entr{'y' if len(merged) == 1 else 'ies'} after merge. "
                f"History tab refreshed."
            )

        def _on_pull_error(msg):
            self.btn_pull_cloud.setEnabled(True)
            self.btn_push_cloud.setEnabled(True)
            self.btn_pull_cloud.setText("⬇  Pull from Cloud")
            QMessageBox.critical(self, "Pull Failed",
                                 f"Could not pull from Supabase:\n{msg}")

        sync_manager.pull_and_merge_history(local,
                                            on_done=_on_pulled,
                                            on_error=_on_pull_error)

    # ----------------------------------------------------------
    # Resume Style
    # ----------------------------------------------------------
    def _on_style_selected(self, key: str):
        """Called on card click — persist immediately."""
        cfg = _load_config()
        cfg["resume_style"] = key
        _save_config(cfg)
        try:
            from services.sync_manager import sync_manager
            import services.theme_manager as tm
            theme = "dark" if tm.theme_manager and tm.theme_manager.is_dark_mode() else "light"
            prefs = cfg.get("default_prefs", {})
            prefs["resume_style"] = key
            sync_manager.push_preferences(theme, prefs)
        except Exception as e:
            print(f"[SETTINGS] Failed to push style to cloud: {e}")

    def _save_style(self):
        """Explicit Save button — confirms and pushes current selection."""
        key = self.style_picker.selected_key()
        cfg = _load_config()
        cfg["resume_style"] = key
        _save_config(cfg)
        try:
            from services.sync_manager import sync_manager
            import services.theme_manager as tm
            theme = "dark" if tm.theme_manager and tm.theme_manager.is_dark_mode() else "light"
            prefs = cfg.get("default_prefs", {})
            prefs["resume_style"] = key
            sync_manager.push_preferences(theme, prefs)
        except Exception as e:
            print(f"[SETTINGS] Failed to push style to cloud: {e}")
        QMessageBox.information(self, "Saved", "Style preference saved.")

    def get_selected_style(self) -> str:
        """Return the currently selected style key (for export logic)."""
        return self.style_picker.selected_key()

    def _set_synced_now(self):

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.lbl_sync_status.setText(f"Last synced: {now}")
        cfg = _load_config()
        cfg["last_synced"] = now
        _save_config(cfg)