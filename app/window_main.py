# app/window_main.py
"""
Main Window Controller for JobFit Pro
-------------------------------------

This file contains ALL logic and event binding for the main desktop app.

Responsibilities:
- Block app startup until authentication succeeds
- Load resume (PDF/DOCX) and job descriptions (URL or manual)
- Trigger LLM-powered resume tailoring
- Manage loading overlay animation
- Handle export to DOCX/PDF
- Save tailoring history (local JSON + Supabase upload)
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

# ---------------- CORE LOGIC MODULES ----------------
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description

from core.uploader.supabase_uploader import upload_resume
from core.exporter.docx_builder import export_to_docx
from core.exporter.pdf_exporter import export_to_pdf
from core.processor.tailor_engine import ResumeTailor

# ---------------- AUTH SYSTEM -----------------------
from services.auth_manager import auth          # Shared singleton
from app.ui.auth_modal import AuthModal         # Login modal

# ---------------- HISTORY --------------------------
from app.ui.tailoring_history_window import HISTORY_FILE


class MainWindow(QMainWindow):
    """
    Main application window (logic layer).
    UI widgets are constructed in ui/main_window.py and attached here.
    """

    def __init__(self) -> None:
        super().__init__()

        print("Creating MainWindow...")

        # Track authenticated state
        self.auth_ok: bool = False
        self.auth = auth
        self.user = self.auth.get_user()

        # ============================================================
        # 1. AUTHENTICATION BLOCKER
        # ============================================================
        if not self.user:
            modal = AuthModal(self)
            result = modal.exec()

            # If declined → app closes in main.py
            if result != QDialog.DialogCode.Accepted:
                return

            self.user = self.auth.get_user()

        if not self.user:
            print("AUTH FAILED: No valid Supabase session returned.")
            return

        self.auth_ok = True
        print("MainWindow created, user:", self.user.email if self.user else None)

        # ============================================================
        # 2. LOADING OVERLAY SETUP
        # ============================================================
        self._loading_base_text = "Tailoring in progress"
        self._loading_dots = 0

        self.loadingLabel = QLabel(self)
        self.loadingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loadingLabel.setStyleSheet("""
            QLabel {
                background-color: rgba(15, 23, 42, 220);
                color: #E5E7EB;
                font-size: 18pt;
                font-weight: 600;
                border-radius: 16px;
                padding: 20px 32px;
            }
        """)
        self.loadingLabel.hide()

        # Dot animation timer
        self.loadingTimer = QTimer(self)
        self.loadingTimer.setInterval(400)
        self.loadingTimer.timeout.connect(self._update_loading_text)

        self._center_loading_label()

        # ============================================================
        # 3. LOAD UI FROM PURE LAYOUT CLASS
        # ============================================================
        from app.ui.main_window import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ============================================================
        # 4. INTERNAL STATE
        # ============================================================
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""

        self.tailor = ResumeTailor()

        # ============================================================
        # 5. CONNECT UI EVENTS
        # ============================================================
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_docx_output)
        self.ui.btnExportPDF.clicked.connect(self.export_pdf_output)
        self.ui.btnUseManualJob.clicked.connect(self.use_manual_job_description)

        # File picker emits → load resume
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

        # ============================================================
        # 6. MENU BAR SETUP
        # ============================================================
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Tools menu
        tools_menu = QMenu("Tools", self)
        menubar.addMenu(tools_menu)

        action_hist = QAction("Tailoring History", self)
        tools_menu.addAction(action_hist)
        action_hist.triggered.connect(self.open_tailoring_history)

        # Right-aligned account menu
        self._setup_user_menu()

    # ==================================================================
    # USER MENU (TOP RIGHT)
    # ==================================================================
    def _setup_user_menu(self) -> None:
        menubar = self.menuBar()

        # Spacer to push account menu right
        spacer = menubar.addMenu(" " * 200)
        spacer.setDisabled(True)

        email = getattr(self.user, "email", "Account")
        account_menu = menubar.addMenu(email)

        logout_action = QAction("Sign Out", self)
        logout_action.triggered.connect(self._sign_out)
        account_menu.addAction(logout_action)

    def _sign_out(self) -> None:
        """Log out user and close app."""
        self.auth.sign_out()
        QMessageBox.information(self, "Signed Out", "You have been signed out.")
        QApplication.instance().quit()

    # ==================================================================
    # LOADING OVERLAY HELPERS
    # ==================================================================
    def _center_loading_label(self):
        w = max(320, int(self.width() * 0.4))
        h = 80
        x = (self.width() - w) // 2
        y = (self.height() - h) // 2
        self.loadingLabel.setGeometry(x, y, w, h)

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
        """Cycle dots in loading text."""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self.loadingLabel.setText(f"{self._loading_base_text}{dots}")

    # ==================================================================
    # RESUME LOADING
    # ==================================================================
    def load_resume_from_picker(self, fname: str):
        if not fname:
            return

        if fname.lower().endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)

        self.ui.resumePreview.setPlainText(self.resume_text)

    # ==================================================================
    # JOB DESCRIPTION FETCH
    # ==================================================================
    def fetch_job(self):
        url = self.ui.inputJobURL.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a job URL.")
            return

        desc = fetch_job_description(url)
        if not desc:
            QMessageBox.warning(self, "Error", "Could not fetch job description.")
            return

        self.job_text = desc
        self.ui.jobPreview.setPlainText(desc)

    # ==================================================================
    # MANUAL JOB DESCRIPTION
    # ==================================================================
    def use_manual_job_description(self):
        txt = self.ui.jobPreview.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "Error", "Paste a job description first.")
            return

        self.job_text = txt
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ==================================================================
    # TAILORING LOGIC
    # ==================================================================
    def tailor_resume(self):
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        # Prefer what's CURRENTLY in UI job box
        pasted = self.ui.jobPreview.toPlainText().strip()
        if pasted:
            self.job_text = pasted

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Paste or fetch a job description.")
            return

        # --- Start overlay ---
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
    # EXPORT: DOCX
    # ==================================================================
    def export_docx_output(self):
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Tailored Resume",
            "Tailored_Resume.docx",
            "Word Document (*.docx)",
        )

        if path:
            export_to_docx(self.tailored_text, path)
            QMessageBox.information(self, "Success", "Resume exported successfully!")

    # ==================================================================
    # EXPORT: PDF
    # ==================================================================
    def export_pdf_output(self):
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Tailored Resume",
            "Tailored_Resume.pdf",
            "PDF Files (*.pdf)",
        )

        if path:
            export_to_pdf(self.tailored_text, path)
            QMessageBox.information(self, "Success", "PDF exported successfully!")

    # ==================================================================
    # HISTORY WINDOW
    # ==================================================================
    def open_tailoring_history(self):
        from app.ui.tailoring_history_window import TailoringHistoryWindow
        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    # ==================================================================
    # SAVE HISTORY (LOCAL + SUPABASE UPLOAD)
    # ==================================================================
    def save_tailoring_history(self):
        company, role = self.extract_company_and_role(self.job_text)

        temp_path = os.path.join(os.getcwd(), "last_tailored_resume.docx")
        export_to_docx(self.tailored_text, temp_path)

        resume_url = upload_resume(temp_path) or temp_path

        entry = {
            "company": company,
            "role": role,
            "job_url": self.ui.inputJobURL.text().strip(),
            "resume_url": resume_url,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = []
        except Exception:
            history = []

        history.append(entry)

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

    # ==================================================================
    # WINDOW RESIZE → RECENTER OVERLAY
    # ==================================================================
    def resizeEvent(self, event):
        self._center_loading_label()
        super().resizeEvent(event)

    # ==================================================================
    # COMPANY & ROLE EXTRACTION
    # ==================================================================
    def extract_company_and_role(self, job_text: str):
        if not job_text:
            return "Unknown", "Unknown"

        text = job_text.strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        first = lines[0] if lines else ""

        # Pattern A — "Company — Role"
        pat = r"^(?P<company>.+?)\s*[-–—]\s*(?P<role>.+)$"
        m = re.match(pat, first)
        if m:
            return m.group("company").strip(), m.group("role").strip()

        # Pattern B — "Role: X"
        m = re.search(r"(Title|Role)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
        role = m.group(2).strip() if m else "Unknown"

        # Pattern C — "Company: X"
        m = re.search(r"(Company|Employer|Hiring Company)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
        company = m.group(2).strip() if m else "Unknown"

        # Fallbacks
        if role == "Unknown" and lines:
            role = lines[0]

        if company == "Unknown" and len(lines) > 1:
            company = lines[1]

        return company, role
