"""
Panel for user-adjustible tailoring preferences.
More polished verical layout + logical grouping.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGroupBox, QFormLayout


class SettingsPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Tailoring Options", self)
        form = QFormLayout(group)

        # Checkbox options
        self.chk_focus_keywords = QCheckBox("Emphasize job keywords")
        self.chk_keep_length = QCheckBox("Keep similar length")
        self.chk_limit_pages = QCheckBox("Limit Resume to 1-2 pages")
        self.chk_limit_one = QCheckBox("Limit Resume to 1 page")
        self.chk_ats_friendly = QCheckBox("ATS-friendly formatting")
        self.chk_ats_friendly.setChecked(True)

        # Add in form layout
        form.addRow(self.chk_focus_keywords)
        form.addRow(self.chk_keep_length)
        form.addRow(self.chk_limit_pages)
        form.addRow(self.chk_limit_one)
        form.addRow(self.chk_ats_friendly)

        outer.addWidget(group)

        # Enforce Mutual Exclusivity
        self.chk_limit_pages.toggled.connect(self._handle_page_limit_change)
        self.chk_limit_one.toggled.connect(self._handle_page_limit_change)

    # -------------------------------------------------------------------------------------
    def _handle_page_limit_change(self):
        """Ensure page-limit settings cannot conflict."""
        if self.chk_limit_pages.isChecked():
            self.chk_limit_one.setChecked(False)
        if self.chk_limit_one.isChecked():
            self.chk_limit_pages.setChecked(False)

    # -------------------------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return settings in a clean dictionary"""
        return {
            "focus_keywords": self.chk_focus_keywords.isChecked(),
            "focus_keywords": self.chk_keep_length.isChecked(),
            "focus_keywords": self.chk_limit_pages.isChecked(),
            "focus_keywords": self.chk_limit_one.isChecked(),
            "focus_keywords": self.chk_ats_friendly.isChecked(),
        }
