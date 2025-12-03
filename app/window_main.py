"""
Main Window Controller for JobFit Pro
-------------------------------------
Handles:
- Resume loading (PDF/DOCX)
- Job description fetching or manual input
- Resume tailoring via LLM
- DOCX & PDF exporting
- Loading overlays
- Tailoring history logging
"""

import os
import re
import json
from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QLabel,
    QApplication,
    QMenuBar,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

# --- Core logic modules ---
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description

from core.exporter.docx_builder import export_to_docx
from core.exporter.pdf_exporter import export_to_pdf
from core.processor.tailor_engine import ResumeTailor

# --- History file ---
from app.ui.tailoring_history_window import HISTORY_FILE


class MainWindow(QMainWindow):
    """
    Main application window for JobFit Pro.
    Manages UI actions, state, loading overlays, and history persistence.
    """

    def __init__(self):
        super().__init__()

        # Load UI Layout
        from app.ui.main_window import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ------------------------------------------------------------
        # Internal State
        # ------------------------------------------------------------
        self.resume_text = ""  # Raw extracted resume content
        self.job_text = ""  # Raw job description
        self.tailored_text = ""  # Tailored resume output
        self.tailor = ResumeTailor()

        # ------------------------------------------------------------
        # UI Event Bindings
        # ------------------------------------------------------------
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_docx_output)
        self.ui.btnExportPDF.clicked.connect(self.export_pdf_output)
        self.ui.btnUseManualJob.clicked.connect(self.use_manual_job_description)
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

        # ------------------------------------------------------------
        # Menu Bar
        # ------------------------------------------------------------
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        tools_menu = QMenu("Tools", self)
        menubar.addMenu(tools_menu)

        # Tailoring History action
        self.action_history = QAction("Tailoring History", self)
        tools_menu.addAction(self.action_history)
        self.action_history.triggered.connect(self.open_tailoring_history)

        # ------------------------------------------------------------
        # Loading Overlay
        # ------------------------------------------------------------
        self._loading_base_text = "Tailoring in progress"
        self._loading_dots = 0

        self.loadingLabel = QLabel(self)
        self.loadingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loadingLabel.setStyleSheet(
            """
            QLabel {
                background-color: rgba(15, 23, 42, 220);
                color: #E5E7EB;
                font-size: 18pt;
                font-weight: 600;
                border-radius: 16px;
                padding: 20px 32px;
            }
            """
        )
        self.loadingLabel.hide()

        # Timer animates the ellipsis (…) while AI processes
        self.loadingTimer = QTimer(self)
        self.loadingTimer.setInterval(400)
        self.loadingTimer.timeout.connect(self._update_loading_text)

        self._center_loading_label()

    # ======================================================================
    # Loading Overlay
    # ======================================================================

    def _center_loading_label(self):
        """Center the loading overlay label relative to window size."""
        width = max(320, int(self.width() * 0.4))
        height = 80
        x = (self.width() - width) // 2
        y = (self.height() - height) // 2
        self.loadingLabel.setGeometry(x, y, width, height)

    def _set_loading_visible(self, visible: bool):
        """Show or hide the loading overlay."""
        if visible:
            self._loading_dots = 0
            self._update_loading_text()
            self._center_loading_label()

            self.loadingLabel.show()
            self.loadingTimer.start()

            # Forces UI to update before LLM work begins
            QApplication.processEvents()

        else:
            self.loadingTimer.stop()
            self.loadingLabel.hide()

    def _update_loading_text(self):
        """Animate 'Tailoring in progress...' with dot cycling."""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self.loadingLabel.setText(f"{self._loading_base_text}{dots}")

    # ======================================================================
    # Resume Loading
    # ======================================================================

    def load_resume_from_picker(self, fname: str):
        """Loads resume text when the file picker selects a file."""
        if not fname:
            return

        if fname.lower().endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)

        self.ui.resumePreview.setPlainText(self.resume_text)

    # ======================================================================
    # Job Description (URL fetch)
    # ======================================================================

    def fetch_job(self):
        """Fetch job description from a URL."""
        url = self.ui.inputJobURL.text().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a job URL.")
            return

        description = fetch_job_description(url)
        if not description:
            QMessageBox.warning(self, "Error", "Could not fetch job description.")
            return

        self.job_text = description
        self.ui.jobPreview.setPlainText(description)

    # ======================================================================
    # Tailoring Logic
    # ======================================================================

    def tailor_resume(self):
        """Perform LLM-powered resume tailoring."""
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        pasted_job = self.ui.jobPreview.toPlainText().strip()
        if pasted_job:
            self.job_text = pasted_job

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Paste or fetch a job description.")
            return

        # Show animated loading overlay
        self._set_loading_visible(True)

        try:
            settings = self.ui.settingsPanel.to_dict()

            self.tailored_text = self.tailor.generate(
                self.resume_text,
                self.job_text,
                limit_pages=settings.get("limit_pages", False),
                limit_one=settings.get("limit_one_page", False),  # <-- FIXED key name
            )

            self.ui.outputPreview.setPlainText(self.tailored_text)

        finally:
            self._set_loading_visible(False)
            self.save_tailoring_history()

    # ======================================================================
    # Export DOCX
    # ======================================================================

    def export_docx_output(self):
        """Export tailored resume as DOCX."""
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Tailored Resume",
            "Tailored_Resume.docx",
            "Word Document (*.docx)",
        )

        if file_path:
            export_to_docx(self.tailored_text, file_path)
            QMessageBox.information(self, "Success", "Resume exported successfully!")

    # ======================================================================
    # Export PDF
    # ======================================================================

    def export_pdf_output(self):
        """Export tailored resume as PDF."""
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Tailored Resume as PDF",
            "Tailored_Resume.pdf",
            "PDF Files (*.pdf)",
        )

        if file_path:
            export_to_pdf(self.tailored_text, file_path)
            QMessageBox.information(self, "Success", "PDF exported successfully!")

    # ======================================================================
    # Manual Job Description Use
    # ======================================================================

    def use_manual_job_description(self):
        """Set pasted job description as active job input."""
        text = self.ui.jobPreview.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "Error", "Paste a job description first.")
            return

        self.job_text = text
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ======================================================================
    # Tailoring History
    # ======================================================================

    def open_tailoring_history(self):
        """Open the Tailoring History window."""
        from app.ui.tailoring_history_window import TailoringHistoryWindow

        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    def save_tailoring_history(self):
        """Store last tailored resume entry to history JSON."""
        company, role = self.extract_company_and_role(self.job_text)

        # Save auto DOCX for history
        auto_path = os.path.join(os.getcwd(), "last_tailored_resume.docx")
        export_to_docx(self.tailored_text, auto_path)

        entry = {"company": company, "role": role, "file": auto_path}

        # Load existing history
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except:
                history = []
        else:
            history = []

        history.append(entry)

        # Save updated list
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    # ======================================================================
    # Window Resize
    # ======================================================================

    def resizeEvent(self, event):
        """Re-center loading overlay when window resizes."""
        self._center_loading_label()
        super().resizeEvent(event)

    # ======================================================================
    # Extract company & role from job text
    # ======================================================================

    def extract_company_and_role(self, job_text: str):
        """
        Extract company and role using regex-based parsing.
        Covers wide variety of job posting formats.
        """

        if not job_text:
            return "Unknown", "Unknown"

        # Normalize text
        text = job_text.strip()

        # -----------------------------------------
        # Pattern 1: "Company – Role" or "Company - Role"
        # -----------------------------------------
        pattern_dash = r"^(?P<company>.+?)\s*[-–—]\s*(?P<role>.+)$"
        match = re.match(pattern_dash, text.split("\n")[0])
        if match:
            return match.group("company").strip(), match.group("role").strip()

        # -----------------------------------------
        # Pattern 2: "Title: XYZ" or "Role: XYZ"
        # -----------------------------------------
        title_pattern = r"(Title|Role)\s*[:\-]\s*(?P<role>.+)"
        match = re.search(title_pattern, text, flags=re.IGNORECASE)
        if match:
            role = match.group("role").split("\n")[0].strip()
        else:
            role = "Unknown"

        # -----------------------------------------
        # Pattern 3: "Company: XYZ", "Employer: XYZ", "Hiring Company: XYZ"
        # -----------------------------------------
        company_pattern = r"(Company|Employer|Hiring Company)\s*[:\-]\s*(?P<company>.+)"
        match = re.search(company_pattern, text, flags=re.IGNORECASE)
        if match:
            company = match.group("company").split("\n")[0].strip()
        else:
            company = "Unknown"

        # -----------------------------------------
        # Fallback — first line = role, second line = company
        # -----------------------------------------
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if role == "Unknown" and len(lines) > 0:
            role = lines[0]
        if company == "Unknown" and len(lines) > 1:
            company = lines[1]

        return company, role
