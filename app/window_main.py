"""
UI logic controller for the application
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QLabel,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer

from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description
from core.exporter.docx_builder import export_to_docx
from core.processor.tailor_engine import ResumeTailor


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        from app.ui.main_window import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # -------------------------------
        # Event Bindings
        # -------------------------------
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_output)
        self.ui.btnUseManualJob.clicked.connect(self.use_manual_job_description)
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

        # -------------------------------
        # State
        # -------------------------------
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""

        # Resume Tailor Engine
        self.tailor = ResumeTailor()

        # -------------------------------
        # Loading Overlay (Text Only)
        # -------------------------------
        self._loading_base_text = "Tailoring in progress"
        self._loading_dots = 0

        self.loadingLabel = QLabel(self)
        self.loadingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loadingLabel.setStyleSheet(
            """
            QLabel {
                background-color: rgba(15, 23, 42, 220); /* slate-900 w/ alpha */
                color: #E5E7EB;                          /* text-slate-200 */
                font-size: 18pt;
                font-weight: 600;
                border-radius: 16px;
                padding: 20px 32px;
            }
            """
        )
        self.loadingLabel.hide()

        # Timer to animate "..." at the end of the text
        self.loadingTimer = QTimer(self)
        self.loadingTimer.setInterval(400)  # ms
        self.loadingTimer.timeout.connect(self._update_loading_text)

        # Initial placement
        self._center_loading_label()

    # ----------------------------------------------------------------------
    # Utility: Center loading label in the window
    # ----------------------------------------------------------------------
    def _center_loading_label(self):
        # We'll make the label a reasonable width portion of the window
        w = int(self.width() * 0.4)
        h = 80
        if w < 320:
            w = 320
        x = self.width() // 2 - w // 2
        y = self.height() // 2 - h // 2

        self.loadingLabel.setGeometry(x, y, w, h)

    # ----------------------------------------------------------------------
    # Utility: Show / hide loading overlay
    # ----------------------------------------------------------------------
    def _set_loading_visible(self, visible: bool):
        if visible:
            self._loading_dots = 0
            self._update_loading_text()
            self._center_loading_label()
            self.loadingLabel.show()
            self.loadingTimer.start()
            QApplication.processEvents()
        else:
            self.loadingTimer.stop()
            self.loadingLabel.hide()

    # ----------------------------------------------------------------------
    # Update "Tailoring in progress..." text with animated dots
    # ----------------------------------------------------------------------
    def _update_loading_text(self):
        self._loading_dots = (self._loading_dots + 1) % 4  # 0..3
        dots = "." * self._loading_dots
        self.loadingLabel.setText(f"{self._loading_base_text}{dots}")

    # ----------------------------------------------------------------------
    # File Picker → Load Resume
    # ----------------------------------------------------------------------
    def load_resume_from_picker(self, fname: str):
        if not fname:
            return

        if fname.endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)

        self.ui.resumePreview.setPlainText(self.resume_text)

    # ----------------------------------------------------------------------
    # Fetch Job From URL
    # ----------------------------------------------------------------------
    def fetch_job(self):
        url = self.ui.inputJobURL.text().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a job URL.")
            return

        self.job_text = fetch_job_description(url)

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Could not fetch job description.")
            return

        self.ui.jobPreview.setPlainText(self.job_text)

    # ----------------------------------------------------------------------
    # Tailor Resume
    # ----------------------------------------------------------------------
    def tailor_resume(self):
        # Ensure resume is loaded
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        pasted_text = self.ui.jobPreview.toPlainText().strip()
        if pasted_text:
            self.job_text = pasted_text

        if not self.job_text:
            QMessageBox.warning(
                self,
                "Error",
                "Please fetch or paste the job description before tailoring.",
            )
            return

        # Show loading overlay
        self._set_loading_visible(True)

        try:
            settings = self.ui.settingsPanel.to_dict()
            limit_pages = settings.get("limit_pages", False)

            tailored = self.tailor.generate(
                self.resume_text,
                self.job_text,
                limit_pages=limit_pages,
            )

            self.tailored_text = tailored
            self.ui.outputPreview.setPlainText(tailored)

        finally:
            # Hide loading overlay
            self._set_loading_visible(False)

    # ----------------------------------------------------------------------
    # Export Tailored Resume
    # ----------------------------------------------------------------------
    def export_output(self):
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        fname, _ = QFileDialog.getSaveFileName(
            self,
            "Save Tailored Resume",
            "Tailored_Resume.docx",
            "Word Document (*.docx)",
        )

        if not fname:
            return

        export_to_docx(self.tailored_text, fname)
        QMessageBox.information(self, "Success", "Resume exported successfully!")

    # ----------------------------------------------------------------------
    # Manual Job Description Mode
    # ----------------------------------------------------------------------
    def use_manual_job_description(self):
        text = self.ui.jobPreview.toPlainText().strip()

        if not text:
            QMessageBox.warning(
                self,
                "Error",
                "Please paste the job description into the Job Description box first.",
            )
            return

        self.job_text = text
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ----------------------------------------------------------------------
    # Keep loading label centered on resize
    # ----------------------------------------------------------------------
    def resizeEvent(self, event):
        self._center_loading_label()
        super().resizeEvent(event)
