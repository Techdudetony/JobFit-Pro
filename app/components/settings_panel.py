"""
SettingsPanel — JobFit Pro
--------------------------

Provides user-adjustable tailoring preferences shown in the left column
of the main UI. Produces a clean SettingsResult object for the
MainWindow controller.

Originally had multiple issues:
- Missing get_settings()
- Duplicated dictionary keys
- Incorrect checkbox attribute names
- No structured settings object

This corrected version resolves all issues.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QGroupBox, QFormLayout


class SettingsResult:
    """
    Container object for tailoring settings.

    Usage:
        settings.limit_pages
        settings.limit_one
        settings.focus_keywords
        settings.ats_friendly
    """

    def __init__(
        self,
        focus_keywords=False,
        keep_length=False,
        limit_pages=False,
        limit_one=False,
        ats_friendly=True,
    ):
        self.focus_keywords = focus_keywords
        self.keep_length = keep_length
        self.limit_pages = limit_pages
        self.limit_one = limit_one
        self.limit_one_page = limit_one
        self.ats_friendly = ats_friendly


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
        self.chk_limit_pages = QCheckBox("Limit resume to 1–2 pages")
        self.chk_limit_one = QCheckBox("Limit resume to 1 page")
        self.chk_ats_friendly = QCheckBox("ATS-friendly formatting")
        self.chk_ats_friendly.setChecked(True)

<<<<<<< HEAD
        inner.addWidget(self.chk_focus_keywords)
        inner.addWidget(self.chk_keep_length)
        inner.addWidget(self.chk_limit_pages)
        inner.addWidget(self.chk_limit_one)
        inner.addWidget(self.chk_ats_friendly)
        inner.addStretch()
        
        # Make page limit checkboxes mutually exclusive
        self.chk_limit_pages.toggled.connect(
            lambda checked: self.chk_limit_one.setEnabled(not checked)
        )
        self.chk_limit_one.toggled.connect(
            lambda checked: self.chk_limit_pages.setEnabled(not checked)
        )
=======
        # Add in form layout
        form.addRow(self.chk_focus_keywords)
        form.addRow(self.chk_keep_length)
        form.addRow(self.chk_limit_pages)
        form.addRow(self.chk_limit_one)
        form.addRow(self.chk_ats_friendly)
>>>>>>> de3b892959d22a9ace277e0b716d2ffd3b568763

        outer.addWidget(group)

        # Enforce mutual exclusivity between the two page-limit options
        self.chk_limit_pages.toggled.connect(self._handle_page_limit_change)
        self.chk_limit_one.toggled.connect(self._handle_page_limit_change)

    # ---------------------------------------------------------
    def _handle_page_limit_change(self):
        """Ensure page-limit settings cannot conflict."""
        if self.chk_limit_pages.isChecked():
            self.chk_limit_one.setChecked(False)
        elif self.chk_limit_one.isChecked():
            self.chk_limit_pages.setChecked(False)

    # ---------------------------------------------------------
    def get_settings(self) -> SettingsResult:
        """
        Returns a structured SettingsResult object used
        by the MainWindow controller.
        """
        return SettingsResult(
            focus_keywords=self.chk_focus_keywords.isChecked(),
            keep_length=self.chk_keep_length.isChecked(),
            limit_pages=self.chk_limit_pages.isChecked(),
            limit_one=self.chk_limit_one.isChecked(),
            ats_friendly=self.chk_ats_friendly.isChecked(),
        )

    # OPTIONAL — your controller no longer uses this, but provided for completeness
    def to_dict(self) -> dict:
        return {
            "focus_keywords": self.chk_focus_keywords.isChecked(),
            "keep_length": self.chk_keep_length.isChecked(),
            "limit_pages": self.chk_limit_pages.isChecked(),
            "limit_one": self.chk_limit_one.isChecked(),
            "ats_friendly": self.chk_ats_friendly.isChecked(),
        }
