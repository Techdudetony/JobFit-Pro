# app/ui/main_window.py
"""
Pure-Python UI definition for the main window.

Layout (top to bottom):
  ROW 1: Job URL input | Fetch Description | Use Pasted Text
  ROW 2: Tailoring Options (horizontal checkboxes)
  ROW 3: Resume: [input] | Browse | Last Resume
  ROW 4: Job Description preview | Original Resume preview  (side by side)
  ROW 5: Tailored Resume output panel (full width)
  ROW 6: Tailor Resume | Export DOCX | Export PDF
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QGroupBox,
)
from PyQt6.QtCore import Qt

from app.components.file_picker import FilePicker
from app.components.output_panel import OutputPanel
from app.components.settings_panel import SettingsPanel


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        MainWindow.setWindowTitle("JobFit Pro")
        MainWindow.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # ---------------------------------------------------------------
        # ROOT
        # ---------------------------------------------------------------
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName("MainCentral")
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self.central_widget)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # ---------------------------------------------------------------
        # ROW 1 — Job URL + buttons
        # ---------------------------------------------------------------
        row_job_url = QHBoxLayout()
        row_job_url.setSpacing(8)

        self.inputJobURL = QLineEdit(self.central_widget)
        self.inputJobURL.setPlaceholderText("Paste job URL here…")
        self.inputJobURL.setObjectName("inputJobURL")

        self.btnFetchJob = QPushButton("Fetch Description", self.central_widget)
        self.btnFetchJob.setObjectName("btnFetchJob")

        self.btnUseManualJob = QPushButton("Use Pasted Text", self.central_widget)
        self.btnUseManualJob.setObjectName("btnUseManualJob")
        self.btnUseManualJob.setProperty("panelButton", True)

        row_job_url.addWidget(self.inputJobURL)
        row_job_url.addWidget(self.btnFetchJob)
        row_job_url.addWidget(self.btnUseManualJob)
        root.addLayout(row_job_url)

        # ---------------------------------------------------------------
        # ROW 2 — Tailoring Options (horizontal checkboxes)
        # ---------------------------------------------------------------
        self.settingsPanel = SettingsPanel(self.central_widget)
        self.settingsPanel.setObjectName("settingsPanel")
        root.addWidget(self.settingsPanel)

        # ---------------------------------------------------------------
        # ROW 3 — Resume file picker + Last Resume button
        # ---------------------------------------------------------------
        row_resume_picker = QHBoxLayout()
        row_resume_picker.setSpacing(8)

        self.resumePicker = FilePicker(
            label_text="Resume:",
            file_filter="PDF or Word (*.pdf *.docx)",
            parent=self.central_widget,
        )
        self.resumePicker.setObjectName("resumePicker")

        self.btnLastResume = QPushButton("↩ Last Resume", self.central_widget)
        self.btnLastResume.setObjectName("btnLastResume")
        self.btnLastResume.setProperty("panelButton", True)
        self.btnLastResume.setVisible(False)

        row_resume_picker.addWidget(self.resumePicker, stretch=1)
        row_resume_picker.addWidget(self.btnLastResume)
        root.addLayout(row_resume_picker)

        # ---------------------------------------------------------------
        # ROW 4 — Job Description | Original Resume (side by side)
        # ---------------------------------------------------------------
        row_previews = QHBoxLayout()
        row_previews.setSpacing(12)

        job_group = QGroupBox("Job Description", self.central_widget)
        job_group.setObjectName("jobPreviewGroup")
        job_group_layout = QVBoxLayout(job_group)
        self.jobPreview = QPlainTextEdit(job_group)
        self.jobPreview.setPlaceholderText("Fetched or pasted job description will appear here…")
        self.jobPreview.setObjectName("jobPreview")
        job_group_layout.addWidget(self.jobPreview)

        resume_group = QGroupBox("Original Resume", self.central_widget)
        resume_group.setObjectName("resumePreviewGroup")
        resume_group_layout = QVBoxLayout(resume_group)
        self.resumePreview = QPlainTextEdit(resume_group)
        self.resumePreview.setPlaceholderText("Loaded resume text will appear here…")
        self.resumePreview.setObjectName("resumePreview")
        resume_group_layout.addWidget(self.resumePreview)

        row_previews.addWidget(job_group)
        row_previews.addWidget(resume_group)
        root.addLayout(row_previews, stretch=3)

        # ---------------------------------------------------------------
        # ROW 5 — Tailored Resume output (full width)
        # ---------------------------------------------------------------
        output_group = QGroupBox("Tailored Resume", self.central_widget)
        output_group.setObjectName("tailoredGroup")
        output_group_layout = QVBoxLayout(output_group)

        self.outputPanel = OutputPanel(parent=output_group)
        self.outputPanel.setObjectName("outputPanel")
        self.outputPreview = self.outputPanel.text_edit  # expose for controller

        output_group_layout.addWidget(self.outputPanel)
        root.addWidget(output_group, stretch=2)

        # ---------------------------------------------------------------
        # ROW 6 — CTA buttons
        # ---------------------------------------------------------------
        row_actions = QHBoxLayout()
        row_actions.setSpacing(8)
        row_actions.addStretch()

        self.btnTailor = QPushButton("Tailor Resume", self.central_widget)
        self.btnTailor.setObjectName("btnTailor")

        self.btnExport = QPushButton("Export DOCX", self.central_widget)
        self.btnExport.setObjectName("btnExportDOCX")
        self.btnExport.setProperty("panelButton", True)

        self.btnExportPDF = QPushButton("Export PDF", self.central_widget)
        self.btnExportPDF.setObjectName("btnExportPDF")
        self.btnExportPDF.setProperty("panelButton", True)

        row_actions.addWidget(self.btnTailor)
        row_actions.addWidget(self.btnExport)
        row_actions.addWidget(self.btnExportPDF)
        root.addLayout(row_actions)

        MainWindow.setCentralWidget(self.central_widget)