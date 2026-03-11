"""
Pure-Python UI definition for the main window.

This file builds the **static widget tree only**.
- No business logic
- No Supabase logic
- No file parsing logic

QSS styling hooks have been added for visual theme control.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QGroupBox,
)
from PyQt6.QtCore import Qt

from app.components.file_picker import FilePicker
from app.components.output_panel import OutPutPanel
from app.components.settings_panel import SettingsPanel


class Ui_MainWindow(object):
    """
    Pure UI definition for JobFit Pro.

    NOTE:
    - This class NEVER contains logic.
    - MainWindow handles signals, events, Supabase calls, etc.
    - QSS objectNames added for styling consistency.
    """

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 800)
        MainWindow.setWindowTitle("JobFit Pro")
        MainWindow.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # ===============================================================
        # ROOT CONTAINER
        # ===============================================================
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName("MainCentral")
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(12, 12, 12, 12)
        self.central_layout.setSpacing(10)

        # ===============================================================
        # ROW 1 — Job URL + buttons
        # ===============================================================
        job_row = QHBoxLayout()
        job_row.setSpacing(8)

        lbl_job_url = QLabel("Job URL:", self.central_widget)
        lbl_job_url.setObjectName("labelJobUrl")

        self.inputJobURL = QLineEdit(self.central_widget)
        self.inputJobURL.setPlaceholderText("Paste the job posting URL here...")
        self.inputJobURL.setObjectName("inputJobURL")

        self.btnUseManualJob = QPushButton("Use Pasted Text", self.central_widget)
        self.btnUseManualJob.setObjectName("btnUseManualJob")
        self.btnUseManualJob.setProperty("variant", "secondary")

        self.btnFetchJob = QPushButton("Fetch Description", self.central_widget)
        self.btnFetchJob.setObjectName("btnFetchJob")
        self.btnFetchJob.setProperty("variant", "primary")

        job_row.addWidget(lbl_job_url)
        job_row.addWidget(self.inputJobURL)
        job_row.addWidget(self.btnUseManualJob)
        job_row.addWidget(self.btnFetchJob)

        self.central_layout.addLayout(job_row)

        # ===============================================================
        # ROW 2 — Settings Panel
        # ===============================================================
        self.settingsPanel = SettingsPanel(self.central_widget)
        self.settingsPanel.setObjectName("settingsPanel")
        self.central_layout.addWidget(self.settingsPanel)

        # ===============================================================
        # ROW 3 — Resume File Picker
        # ===============================================================
        self.resumePicker = FilePicker(
            label_text="Resume:",
            file_filter="PDF or Word (*.pdf *.docx)",
            parent=self.central_widget,
        )
        self.resumePicker.setObjectName("resumePicker")

        # Expose Browse button so MainWindow can connect signals
        self.btnLoadResume = self.resumePicker.button

        self.central_layout.addWidget(self.resumePicker)

        # ===============================================================
        # ROW 4 — Job + Resume Preview Side by Side
        # ===============================================================
        previews_row = QHBoxLayout()
        previews_row.setSpacing(12)

        # ----- JOB DESCRIPTION GROUP -----
        job_group = QGroupBox("Job Description", self.central_widget)
        job_group.setObjectName("jobPreviewGroup")
        job_group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        job_group_layout = QVBoxLayout(job_group)
        self.jobPreview = QPlainTextEdit(job_group)
        self.jobPreview.setPlaceholderText(
            "Fetched or pasted job description will appear here..."
        )
        self.jobPreview.setObjectName("jobPreview")
        job_group_layout.addWidget(self.jobPreview)

        # ----- RESUME PREVIEW GROUP -----
        resume_group = QGroupBox("Original Resume", self.central_widget)
        resume_group.setObjectName("resumePreviewGroup")
        resume_group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        resume_group_layout = QVBoxLayout(resume_group)
        self.resumePreview = QPlainTextEdit(resume_group)
        self.resumePreview.setPlaceholderText("Loaded resume text will appear here...")
        self.resumePreview.setObjectName("resumePreview")
        resume_group_layout.addWidget(self.resumePreview)

        previews_row.addWidget(job_group)
        previews_row.addWidget(resume_group)
        self.central_layout.addLayout(previews_row)

        # ===============================================================
        # ROW 5 — Tailored Resume Output Panel
        # ===============================================================
        output_group = QGroupBox("Tailored Resume", self.central_widget)
        output_group.setObjectName("tailoredGroup")
        output_group.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        output_group_layout = QVBoxLayout(output_group)

        # Custom component
        self.outputPanel = OutPutPanel(parent=output_group)
        self.outputPanel.setObjectName("outputPanel")

        # Expose text edit for MainWindow logic
        self.outputPreview = self.outputPanel.text_edit

        output_group_layout.addWidget(self.outputPanel)
        self.central_layout.addWidget(output_group)

        # ===============================================================
        # ROW 6 — Action Buttons (RIGHT ALIGNED)
        # ===============================================================
        actions_row = QHBoxLayout()
        actions_row.addStretch()

        self.btnTailor = QPushButton("Tailor Resume", self.central_widget)
        self.btnTailor.setObjectName("btnTailor")
        self.btnTailor.setProperty("variant", "primary")

        self.btnExport = QPushButton("Export DOCX", self.central_widget)
        self.btnExport.setObjectName("btnExportDOCX")
        self.btnExport.setProperty("variant", "secondary")

        self.btnExportPDF = QPushButton("Export PDF", self.central_widget)
        self.btnExportPDF.setObjectName("btnExportPDF")
        self.btnExportPDF.setProperty("variant", "secondary")

        actions_row.addWidget(self.btnTailor)
        actions_row.addWidget(self.btnExport)
        actions_row.addWidget(self.btnExportPDF)

        self.central_layout.addLayout(actions_row)

        # Attach to main window
        MainWindow.setCentralWidget(self.central_widget)
