"""
Panel for user-adjustable tailoring preferences.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGroupBox, QHBoxLayout


class SettingsPanel(QWidget):
    # User-facing settings for tailoring behavior.
    def __init__(self, parent=None):
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Tailoring Options", self)
        inner = QHBoxLayout(group)

        self.chk_focus_keywords = QCheckBox("Emphsize job keywords", group)
        self.chk_keep_length = QCheckBox("Keep similar length", group)
        self.chk_ats_friendly = QCheckBox("ATS-friendly formatting", group)
        self.chk_ats_friendly.setChecked(True)

        inner.addWidget(self.chk_focus_keywords)
        inner.addWidget(self.chk_keep_length)
        inner.addWidget(self.chk_ats_friendly)
        inner.addStretch()

        outer_layout.addWidget(group)

    # --------------------------------------------------------------------------

    def to_dict(self) -> dict:
        # Export current settings as a simple dictionary.
        return {
            "focus_keywords": self.chk_focus_keywords.isChecked(),
            "keep_length": self.chk_keep_length.isChecked(),
            "ats_friendly": self.chk_ats_friendly.isChecked(),
        }
