"""
UI logic controller for the application
"""

from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
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

        # Event Bindings
        self.ui.btnLoadResume.clicked.connect(self.load_resume)
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_output)
        self.ui.btnUseManualJob.clicked.connect(self.use_manual_job_description)

        # Initialize State Variables
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""

        # Initialize the Tailoring Engine
        self.tailor = ResumeTailor()

    # --------------------------------------------------------------------------

    def load_resume(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Resume", "", "PDF Files (*.pdf);;Word Files (*.docx)"
        )

        if not fname:
            return

        if fname.endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)

        self.ui.resumePreview.setPlainText(self.resume_text)

    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------

    def tailor_resume(self):
        # 1. Check resume loaded
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        # 2. Use typed job description if present
        pasted_text = self.ui.jobPreview.toPlainText().strip()
        if pasted_text:
            self.job_text = pasted_text

        # 3. If no typed text AND no fetched text → error
        if not self.job_text:
            QMessageBox.warning(
                self,
                "Error",
                "Please fetch or paste the job description before tailoring.",
            )
            return

        settings = self.ui.settingsPanel.to_dict()
        limit_pages = settings.get("limit_pages", False)

        # 4. Generate tailored resume
        tailored = self.tailor.generate(
            self.resume_text, self.job_text, limit_pages=limit_pages
        )
        self.tailored_text = tailored
        self.ui.outputPreview.setPlainText(tailored)

    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------

    def use_manual_job_description(self):
        # Skip URL fetching and use whatever text the user typed into jobPreview.
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
