"""
Pure-Python UI definition for the main window.
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
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 800)
        MainWindow.setWindowTitle("JobFit Pro")

        # Central Widget + Root Layout
        self.central_widget = QWidget(MainWindow)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(12, 12, 12, 12)
        self.central_layout.setSpacing(10)

        # -------------------------------------------
        # Row 1: Job URL input and Fetch button
        # -------------------------------------------
        job_row = QHBoxLayout()
        lbl_job_url = QLabel("Job URL:", self.central_widget)

        self.inputJobURL = QLineEdit(self.central_widget)
        self.inputJobURL.setPlaceholderText("Paste the job posting URL here...")

        self.btnUseManualJob = QPushButton("Use Pasted Text", self.central_widget)
        self.btnFetchJob = QPushButton("Fetch Description", self.central_widget)

        job_row.addWidget(lbl_job_url)
        job_row.addWidget(self.inputJobURL)
        job_row.addWidget(self.btnUseManualJob)
        job_row.addWidget(self.btnFetchJob)

        self.central_layout.addLayout(job_row)

        # -------------------------------------------
        # Row 2: Tailoring settings panel
        # -------------------------------------------
        self.settingsPanel = SettingsPanel(self.central_widget)
        self.central_layout.addWidget(self.settingsPanel)

        # -------------------------------------------
        # Row 3: Resume file picker
        # -------------------------------------------
        self.resumePicker = FilePicker(
            label_text="Resume:",
            file_filter="PDF or Word (*.pdf *.docx)",
            parent=self.central_widget,
        )
        # Expose the Browse button as btnLoadResume for MainWindow logic
        self.btnLoadResume = self.resumePicker.button

        self.central_layout.addWidget(self.resumePicker)

        # -------------------------------------------
        # Row 4. Job + Resume previews side by side
        # -------------------------------------------
        previews_row = QHBoxLayout()

        # Job Description Preview
        job_group = QGroupBox("Job Description", self.central_widget)
        job_group_layout = QVBoxLayout(job_group)
        self.jobPreview = QPlainTextEdit(job_group)
        self.jobPreview.setPlaceholderText(
            "Fetched or pasted job description will appear here..."
        )
        job_group_layout.addWidget(self.jobPreview)

        # Resume Preview
        resume_group = QGroupBox("Original Resume", self.central_widget)
        resume_group_layout = QVBoxLayout(resume_group)
        self.resumePreview = QPlainTextEdit(resume_group)
        self.resumePreview.setPlaceholderText("Loaded resume text will appear here...")
        resume_group_layout.addWidget(self.resumePreview)

        previews_row.addWidget(job_group)
        previews_row.addWidget(resume_group)

        self.central_layout.addLayout(previews_row)

        # -------------------------------------------
        # Row 5: Tailored Resume Output
        # -------------------------------------------
        output_group = QGroupBox("Tailored Resume", self.central_widget)
        output_group_layout = QVBoxLayout(output_group)

        self.outputPanel = OutPutPanel(parent=output_group)
        # Expose underlying text edit as outputPreview for MainWindow logic
        self.outputPreview = self.outputPanel.text_edit

        output_group_layout.addWidget(self.outputPanel)
        self.central_layout.addWidget(output_group)

        # -------------------------------------------
        # Row 6: Action Buttons
        # -------------------------------------------
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        self.btnTailor = QPushButton("Tailor Resume", self.central_widget)
        self.btnExport = QPushButton("Export DOCX", self.central_widget)
        actions_row.addWidget(self.btnTailor)
        actions_row.addWidget(self.btnExport)

        self.central_layout.addLayout(actions_row)

        MainWindow.setCentralWidget(self.central_widget)
