# app/window_main.py
"""
Main Window Controller for JobFit Pro
-------------------------------------
Responsibilities:
- Enforce authentication on app launch (AuthModal + AuthManager singleton)
- Load resume (PDF/DOCX) and job description (URL or pasted)
- Call LLM-powered tailoring engine
- Export tailored resume to DOCX / PDF
- Show animated loading overlay while tailoring runs
- Save tailoring history (local JSON + Supabase-uploaded resume URL)
"""

import os
import re
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog,
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

# --- Auth + login modal ---
from services.auth_manager import auth  # <- GLOBAL singleton
from app.ui.auth_modal import AuthModal

# --- Local history JSON (used by TailoringHistoryWindow) ---
from app.ui.tailoring_history_window import HISTORY_FILE


class MainWindow(QMainWindow):
    """
    Main application window for JobFit Pro.
    Controls UI events, tailoring behavior, authentication integration,
    export logic, and history tracking.
    """

    def __init__(self) -> None:
        super().__init__()

        # Will be set to True only if authentication succeeds
        self.auth_ok: bool = False

        # Store reference to the shared AuthManager singleton
        self.auth = auth
        self.user = self.auth.get_user()  # May be None if no session yet

        # ------------------------------------------------------------
        # 1) Authentication gate: require login BEFORE we proceed
        # ------------------------------------------------------------
        if not self.user:
            # Show blocking Auth modal
            modal = AuthModal(self)
            result = modal.exec()

            # If user cancels/closes the modal, do not continue init
            if result != QDialog.DialogCode.Accepted:
                # auth_ok stays False; main.py will exit app
                return

            # After successful sign-in, refresh user info
            self.user = self.auth.get_user()

        # If for ANY reason we still don't have a user, abort
        if not self.user:
            return

        # At this point we have a valid authenticated user
        self.auth_ok = True

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

        # Timer to animate "..." at end of text
        self.loadingTimer = QTimer(self)
        self.loadingTimer.setInterval(400)
        self.loadingTimer.timeout.connect(self._update_loading_text)

        # Initial centering of loading overlay
        self._center_loading_label()

        # ------------------------------------------------------------
        # 2) Load main UI layout (from Designer-generated class)
        # ------------------------------------------------------------
        from app.ui.main_window import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ------------------------------------------------------------
        # Internal state
        # ------------------------------------------------------------
        self.resume_text: str = ""  # Raw extracted resume
        self.job_text: str = ""  # Job description (fetched or pasted)
        self.tailored_text: str = ""  # Tailored resume result from LLM

        self.tailor = ResumeTailor()  # LLM tailoring engine

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
        # Menu Bar (Tools → Tailoring History + User Menu)
        # ------------------------------------------------------------
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Tools menu
        tools_menu = QMenu("Tools", self)
        menubar.addMenu(tools_menu)

        # Tailoring History action
        self.action_history = QAction("Tailoring History", self)
        tools_menu.addAction(self.action_history)
        self.action_history.triggered.connect(self.open_tailoring_history)

        # User account menu (right aligned)
        self._setup_user_menu()

    # ==================================================================
    # User Menu (Top-right)
    # ==================================================================
    def _setup_user_menu(self) -> None:
        """
        Adds a right-aligned user menu to the menu bar that:
        - Shows the current user's email
        - Offers a 'Sign Out' option
        """
        menubar = self.menuBar()

        # Spacer menu forces the user menu all the way to the right
        spacer = menubar.addMenu(" " * 200)
        spacer.setDisabled(True)

        # Display user email or generic label
        email = getattr(self.user, "email", None) or "Account"
        self.user_menu = menubar.addMenu(email)

        # Sign Out action
        logout_action = QAction("Sign Out", self)
        logout_action.triggered.connect(self._sign_out)
        self.user_menu.addAction(logout_action)

    def _sign_out(self) -> None:
        """
        Logs the user out and closes the application.
        (On next launch, the AuthModal will appear again.)
        """
        self.auth.sign_out()
        QMessageBox.information(self, "Signed Out", "You have been signed out.")
        app = QApplication.instance()
        if app is not None:
            app.quit()

    # ==================================================================
    # Loading overlay helpers
    # ==================================================================
    def _center_loading_label(self) -> None:
        """Position loading overlay label in the center of the window."""
        width = max(320, int(self.width() * 0.4))
        height = 80
        x = (self.width() - width) // 2
        y = (self.height() - height) // 2
        self.loadingLabel.setGeometry(x, y, width, height)

    def _set_loading_visible(self, visible: bool) -> None:
        """Show or hide the animated loading overlay."""
        if visible:
            self._loading_dots = 0
            self._update_loading_text()
            self._center_loading_label()
            self.loadingLabel.show()
            self.loadingTimer.start()
            QApplication.processEvents()  # Let UI repaint before heavy work
        else:
            self.loadingTimer.stop()
            self.loadingLabel.hide()

    def _update_loading_text(self) -> None:
        """Animate 'Tailoring in progress...' with cycling dots."""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self.loadingLabel.setText(f"{self._loading_base_text}{dots}")

    # ==================================================================
    # Resume loading
    # ==================================================================
    def load_resume_from_picker(self, fname: str) -> None:
        """
        Called when the file picker fires fileSelected.
        Extracts text from PDF or DOCX and pushes it into the UI.
        """
        if not fname:
            return

        if fname.lower().endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)

        self.ui.resumePreview.setPlainText(self.resume_text)

    # ==================================================================
    # Fetch job description
    # ==================================================================
    def fetch_job(self) -> None:
        """
        Fetch job description from the URL in the Job URL field
        and populate the Job Description preview box.
        """
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

    # ==================================================================
    # Tailoring logic
    # ==================================================================
    def tailor_resume(self) -> None:
        """
        Orchestrates the end-to-end tailoring:
        - Uses loaded resume text
        - Uses fetched or pasted job description
        - Calls the LLM engine with current settings
        - Displays output and logs history
        """
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        pasted_job = self.ui.jobPreview.toPlainText().strip()
        if pasted_job:
            self.job_text = pasted_job

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Paste or fetch a job description.")
            return

        # Show animated overlay
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

    # ==================================================================
    # Export DOCX
    # ==================================================================
    def export_docx_output(self) -> None:
        """Export the tailored resume text to a DOCX file."""
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

    # ==================================================================
    # Export PDF
    # ==================================================================
    def export_pdf_output(self) -> None:
        """Export the tailored resume text to a PDF file."""
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

    # ==================================================================
    # Manual Job Description (Paste)
    # ==================================================================
    def use_manual_job_description(self) -> None:
        """Use whatever is in the Job Description box as the active job text."""
        text = self.ui.jobPreview.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Paste a job description first.")
            return

        self.job_text = text
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ==================================================================
    # Tailoring History Window
    # ==================================================================
    def open_tailoring_history(self) -> None:
        """Open the Tailoring History dialog window."""
        from app.ui.tailoring_history_window import TailoringHistoryWindow

        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    # ==================================================================
    # Save History (Supabase + Local JSON)
    # ==================================================================
    def save_tailoring_history(self) -> None:
        """
        Save last tailoring session to:
        - Local JSON (for TailoringHistoryWindow UI)
        - Supabase Storage (via upload_resume → returns URL)
        """
        company, role = self.extract_company_and_role(self.job_text)

        # Create a local temporary DOCX
        temp_path = os.path.join(os.getcwd(), "last_tailored_resume.docx")
        export_to_docx(self.tailored_text, temp_path)

        # Upload to Supabase → returns public/signed URL or None
        resume_url = upload_resume(temp_path)

        history_entry = {
            "company": company,
            "role": role,
            "job_url": self.ui.inputJobURL.text().strip(),
            "resume_url": resume_url if resume_url else temp_path,
            "timestamp": datetime.now().isoformat(),
        }

        # --------------------
        # Local JSON persistence
        # --------------------
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = []
        except Exception:
            history = []

        history.append(history_entry)

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

        # If you want to also insert into a Supabase table, do it here.

    # ==================================================================
    # Resize event
    # ==================================================================
    def resizeEvent(self, event) -> None:
        """Re-center loading overlay whenever the window is resized."""
        self._center_loading_label()
        super().resizeEvent(event)

    # ==================================================================
    # Extract company & role using robust regex
    # ==================================================================
    def extract_company_and_role(self, job_text: str):
        """
        Attempts to extract:
            - Company name
            - Job role/title
        Using multiple regex patterns for higher accuracy across formats.
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

        # Pattern 2 — "Title: XYZ" or "Role: XYZ"
        title_pattern = r"(Title|Role)\s*[:\-]\s*(.+)"
        m = re.search(title_pattern, text, re.IGNORECASE)
        role = m.group(2).strip() if m else "Unknown"

        # Pattern 3 — "Company: XYZ", "Employer: XYZ", etc.
        company_pattern = r"(Company|Employer|Hiring Company)\s*[:\-]\s*(.+)"
        m = re.search(company_pattern, text, re.IGNORECASE)
        company = m.group(2).strip() if m else "Unknown"

        # Fallback: first line = role, second line = company
        if role == "Unknown" and len(lines) > 0:
            role = lines[0]
        if company == "Unknown" and len(lines) > 1:
            company = lines[1]

        return company, role
