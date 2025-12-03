"""
Main Window Controller for JobFit Pro
-------------------------------------
Handles:
- Resume loading (PDF/DOCX)
- Job description fetching or manual input
- Resume tailoring via LLM
- DOCX & PDF exporting
- Loading overlays
- Tailoring history logging (JSON + Supabase)
"""

import os
import re
import json
from datetime import datetime

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

# --- Core logic + tools ---
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description

from core.uploader.supabase_uploader import upload_resume
from core.exporter.docx_builder import export_to_docx
from core.exporter.pdf_exporter import export_to_pdf
from core.processor.tailor_engine import ResumeTailor

# --- Local history JSON (fallback + UI history window) ---
from app.ui.tailoring_history_window import HISTORY_FILE


class MainWindow(QMainWindow):
    """
    Main application window for JobFit Pro.
    Controls UI events, model behavior, and history tracking.
    """

    def __init__(self):
        super().__init__()

        # Load main UI file
        from app.ui.main_window import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ------------------------------------------------------------
        # Internal state
        # ------------------------------------------------------------
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""
        self.tailor = ResumeTailor()

        # ------------------------------------------------------------
        # Bind UI events
        # ------------------------------------------------------------
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_docx_output)
        self.ui.btnExportPDF.clicked.connect(self.export_pdf_output)
        self.ui.btnUseManualJob.clicked.connect(self.use_manual_job_description)
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

        # ------------------------------------------------------------
        # Menu Bar (Tools → Tailoring History)
        # ------------------------------------------------------------
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        tools_menu = QMenu("Tools", self)
        menubar.addMenu(tools_menu)

        self.action_history = QAction("Tailoring History", self)
        tools_menu.addAction(self.action_history)
        self.action_history.triggered.connect(self.open_tailoring_history)

        # ------------------------------------------------------------
        # Loading Overlay (animated)
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

        self.loadingTimer = QTimer(self)
        self.loadingTimer.setInterval(400)
        self.loadingTimer.timeout.connect(self._update_loading_text)

        self._center_loading_label()

    # ======================================================================
    # Loading overlay helpers
    # ======================================================================

    def _center_loading_label(self):
        width = max(320, int(self.width() * 0.4))
        height = 80
        x = (self.width() - width) // 2
        y = (self.height() - height) // 2
        self.loadingLabel.setGeometry(x, y, width, height)

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

    def _update_loading_text(self):
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self.loadingLabel.setText(f"{self._loading_base_text}{dots}")

    # ======================================================================
    # Resume loading
    # ======================================================================

    def load_resume_from_picker(self, fname: str):
        if not fname:
            return
        if fname.lower().endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)
        self.ui.resumePreview.setPlainText(self.resume_text)

    # ======================================================================
    # Fetch job description
    # ======================================================================

    def fetch_job(self):
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
    # Tailoring logic
    # ======================================================================

    def tailor_resume(self):
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        pasted_job = self.ui.jobPreview.toPlainText().strip()
        if pasted_job:
            self.job_text = pasted_job

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Paste or fetch a job description.")
            return

        self._set_loading_visible(True)

        try:
            settings = self.ui.settingsPanel.to_dict()

            self.tailored_text = self.tailor.generate(
                self.resume_text,
                self.job_text,
                limit_pages=settings.get("limit_pages", False),
                limit_one=settings.get("limit_one_page", False),
            )

            self.ui.outputPreview.setPlainText(self.tailored_text)

        finally:
            self._set_loading_visible(False)
            self.save_tailoring_history()

    # ======================================================================
    # Export DOCX
    # ======================================================================

    def export_docx_output(self):
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
    # Manual Job Description (Paste)
    # ======================================================================

    def use_manual_job_description(self):
        text = self.ui.jobPreview.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Paste a job description first.")
            return
        self.job_text = text
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ======================================================================
    # Tailoring History Window
    # ======================================================================

    def open_tailoring_history(self):
        from app.ui.tailoring_history_window import TailoringHistoryWindow

        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    # ======================================================================
    # Save History (Supabase + Local JSON)
    # ======================================================================

    def save_tailoring_history(self):
        """Saves last tailoring session to Supabase + local JSON fallback."""
        company, role = self.extract_company_and_role(self.job_text)

        # Create a local temporary file
        temp_path = os.path.join(os.getcwd(), "last_tailored_resume.docx")
        export_to_docx(self.tailored_text, temp_path)

        # Upload to Supabase → returns public URL or None
        resume_url = upload_resume(temp_path)

        history_entry = {
            "company": company,
            "role": role,
            "job_url": self.ui.inputJobURL.text().strip(),
            "resume_url": resume_url if resume_url else temp_path,
            "timestamp": datetime.now().isoformat(),
        }

        # --------------------
        # Local JSON fallback
        # --------------------
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
            else:
                history = []
        except:
            history = []

        history.append(history_entry)

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

        # --------------------
        # Supabase storage (optional)
        # --------------------
        # You already insert into Supabase inside upload_resume() or can insert here.
        # If you want to add a "tailoring_history" table insert here, tell me.

    # ======================================================================
    # Resize event
    # ======================================================================

    def resizeEvent(self, event):
        self._center_loading_label()
        super().resizeEvent(event)

    # ======================================================================
    # Extract company & role using robust regex
    # ======================================================================

    def extract_company_and_role(self, job_text: str):
        """
        Attempts to extract:
            - Company name
            - Job role/title
        Using multiple regex patterns for high accuracy.
        """
        if not job_text:
            return "Unknown", "Unknown"

        text = job_text.strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        first_line = lines[0] if lines else ""

        # Pattern 1 — "Company – Role"
        dash_pattern = r"^(?P<company>.+?)\s*[-–—]\s*(?P<role>.+)$"
        m = re.match(dash_pattern, first_line)
        if m:
            return m.group("company").strip(), m.group("role").strip()

        # Pattern 2 — Title: XYZ
        title_pattern = r"(Title|Role)\s*[:\-]\s*(.+)"
        m = re.search(title_pattern, text, re.IGNORECASE)
        role = m.group(2).strip() if m else "Unknown"

        # Pattern 3 — Company: XYZ
        company_pattern = r"(Company|Employer|Hiring Company)\s*[:\-]\s*(.+)"
        m = re.search(company_pattern, text, re.IGNORECASE)
        company = m.group(2).strip() if m else "Unknown"

        # Fallback: first = role, second = company
        if role == "Unknown" and len(lines) > 0:
            role = lines[0]
        if company == "Unknown" and len(lines) > 1:
            company = lines[1]

        return company, role
