# app/ui/tabs/tab_tailor.py
"""
Tailor Tab — JobFit Pro
-----------------------

Layout:
  ROW 1 (URL bar):  [Job URL input] [Fetch] [Use Pasted Text]
  ROW 2 (options):  Settings panel (horizontal checkboxes)
  ROW 3 (picker):   [FilePicker] [↩ Last Resume]
  ROW 4 (previews): [Job Description] | [Original Resume]   (equal width)
  ROW 5 (output):   Tailored Resume output panel (full width)
  ROW 6 (actions):  [stretch] [Tailor Resume] [Export DOCX] [Export PDF]
"""

import os
import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QGroupBox,
    QLabel,
)
from PyQt6.QtCore import Qt

from app.components.file_picker import FilePicker
from app.components.output_panel import OutputPanel
from app.components.settings_panel import SettingsPanel


class TailorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_saved_prefs()

        # ATS panel overlays this tab
        from app.ui.ats_panel import ATSPanel

        self.atsPanel = ATSPanel(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "atsPanel"):
            self.atsPanel.reposition()

    def _apply_saved_prefs(self):
        """Apply saved default preferences from config.json to settings panel."""
        config_file = os.path.join(os.path.expanduser("~"), ".jobfitpro", "config.json")
        try:
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                prefs = cfg.get("default_prefs", {})
                if prefs:
                    self.settingsPanel.chk_focus_keywords.setChecked(
                        prefs.get("focus_keywords", False)
                    )
                    self.settingsPanel.chk_ats_friendly.setChecked(
                        prefs.get("ats_friendly", True)
                    )
                    self.settingsPanel.chk_keep_length.setChecked(
                        prefs.get("keep_length", False)
                    )
                    self.settingsPanel.chk_limit_one.setChecked(
                        prefs.get("limit_one", False)
                    )
        except Exception:
            pass

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ── ROW 1 — Job URL ──────────────────────────────────────
        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        lbl = QLabel("Job URL:")
        lbl.setObjectName("labelJobUrl")

        self.inputJobURL = QLineEdit()
        self.inputJobURL.setPlaceholderText("Paste the job posting URL here...")
        self.inputJobURL.setObjectName("inputJobURL")

        self.btnUseManualJob = QPushButton("Use Pasted Text")
        self.btnUseManualJob.setObjectName("btnUseManualJob")

        self.btnFetchJob = QPushButton("Fetch Description")
        self.btnFetchJob.setObjectName("btnFetchJob")

        url_row.addWidget(lbl)
        url_row.addWidget(self.inputJobURL, stretch=1)
        url_row.addWidget(self.btnUseManualJob)
        url_row.addWidget(self.btnFetchJob)
        root.addLayout(url_row)

        # ── ROW 2 — Settings panel ───────────────────────────────
        self.settingsPanel = SettingsPanel(self)
        self.settingsPanel.setObjectName("settingsPanel")
        root.addWidget(self.settingsPanel)

        # ── ROW 3 — Resume picker ────────────────────────────────
        picker_row = QHBoxLayout()
        picker_row.setSpacing(8)

        self.resumePicker = FilePicker(
            label_text="Resume:",
            file_filter="PDF or Word (*.pdf *.docx)",
            parent=self,
        )
        self.resumePicker.setObjectName("resumePicker")
        self.btnLoadResume = self.resumePicker.button

        self.btnLastResume = QPushButton("↩ Last Resume")
        self.btnLastResume.setObjectName("btnLastResume")
        self.btnLastResume.setVisible(False)

        picker_row.addWidget(self.resumePicker, stretch=1)
        picker_row.addWidget(self.btnLastResume)
        root.addLayout(picker_row)

        # ── ROW 4 — Job + Resume preview side by side ────────────
        preview_row = QHBoxLayout()
        preview_row.setSpacing(12)

        job_group = QGroupBox("Job Description")
        job_group.setObjectName("jobPreviewGroup")
        job_layout = QVBoxLayout(job_group)
        self.jobPreview = QPlainTextEdit()
        self.jobPreview.setPlaceholderText(
            "Fetched or pasted job description will appear here..."
        )
        self.jobPreview.setObjectName("jobPreview")
        job_layout.addWidget(self.jobPreview)

        resume_group = QGroupBox("Original Resume")
        resume_group.setObjectName("resumePreviewGroup")
        resume_layout = QVBoxLayout(resume_group)
        self.resumePreview = QPlainTextEdit()
        self.resumePreview.setPlaceholderText("Loaded resume text will appear here...")
        self.resumePreview.setObjectName("resumePreview")
        resume_layout.addWidget(self.resumePreview)

        preview_row.addWidget(job_group, stretch=1)
        preview_row.addWidget(resume_group, stretch=1)
        root.addLayout(preview_row, stretch=3)

        # ── ROW 5 — Output panel (full width) ────────────────────
        output_group = QGroupBox("Tailored Resume")
        output_group.setObjectName("tailoredGroup")
        output_layout = QVBoxLayout(output_group)

        self.outputPanel = OutputPanel(parent=output_group)
        self.outputPanel.setObjectName("outputPanel")
        self.outputPreview = self.outputPanel.text_edit

        output_layout.addWidget(self.outputPanel)
        root.addWidget(output_group, stretch=2)

        # ── ROW 6 — Action buttons ────────────────────────────────
        action_row = QHBoxLayout()
        action_row.addStretch()

        self.btnTailor = QPushButton("Tailor Resume")
        self.btnTailor.setObjectName("btnTailor")

        self.btnExport = QPushButton("Export DOCX")
        self.btnExport.setObjectName("btnExport")

        self.btnExportPDF = QPushButton("Export PDF")
        self.btnExportPDF.setObjectName("btnExportPDF")

        action_row.addWidget(self.btnTailor)
        action_row.addWidget(self.btnExport)
        action_row.addWidget(self.btnExportPDF)
        root.addLayout(action_row)
