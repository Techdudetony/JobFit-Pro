"""
Main Application Window Controller
------------------------------------------------------

Coordinates all high-level interactions between the UI, state, and business logic.
- Loads UI (UI_MainWindow)
- Handles resume loading, job fetching, tailoring, exporting
- Manages menus, help dialogs, account actions
- Saves tailoring history using HistoryManager
- Delegates all heavy logic to extractor/processor/uploader modules
"""

from datetime import datetime

from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction

# ----------------------------- APP MODULES ---------------------------------------
from app.state.session_state import SessionState
from core.history.history_manager import HistoryManager
from app.ui.tailoring_history_window import TailoringHistoryWindow, HISTORY_FILE
from app.ui.main_window_ui import Ui_MainWindow

# EXTRACTORS
from core.extractor.job_parser import fetch_job_description
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx

# ML TAILOR
from core.processor.tailor_engine import ResumeTailor

# UPLOADING
from core.uploader.supabase_uploader import upload_resume

# UTILS
from core.history.utils import extract_company_role


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # -----------------------------------------------------------
        # APP STATE + CORE MODULES
        # -----------------------------------------------------------
        self.state = SessionState()
        self.history_manager = HistoryManager(HISTORY_FILE)
        self.tailor_engine = ResumeTailor()

        # -----------------------------------------------------------
        # LOAD UI
        # -----------------------------------------------------------
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # -----------------------------------------------------------
        # MENUS + EVENTS
        # -----------------------------------------------------------
        self._setup_menus()
        self._setup_events()

        self.setWindowTitle("JobFit Pro")

    # ==========================================================
    #   MENU SETUP
    # ==========================================================
    def _setup_menus(self):
        menubar = self.menuBar()

        # -----------------------------------------------------------
        # FILE MENU
        # -----------------------------------------------------------
        file_menu = menubar.addMenu("File")

        action_new = QAction("New Resume", self)
        action_new.triggered.connect(self.new_resume)
        file_menu.addAction(action_new)

        action_load = QAction("Load Resume", self)
        action_load.triggered.connect(self.load_resume_dialog)
        file_menu.addAction(action_load)

        file_menu.addSeparator()

        export_docx = QAction("Export as DOCX", self)
        export_docx.triggered.connect(lambda: self.export_resume("docx"))
        file_menu.addAction(export_docx)

        export_pdf = QAction("Export as PDF", self)
        export_pdf.triggered.connect(lambda: self.export_resume("pdf"))
        file_menu.addAction(export_pdf)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # -----------------------------------------------------------
        # TOOLS MENU
        # -----------------------------------------------------------
        tools_menu = menubar.addMenu("Tools")

        history_action = QAction("Tailoring History", self)
        history_action.triggered.connect(self.open_history)
        tools_menu.addAction(history_action)

        # Future tools (stubs)
        ats_action = QAction("ATS Score Analyzer", self)
        ats_action.triggered.connect(
            lambda: QMessageBox.information(
                self, "Coming Soon", "ATS scoring will be available in a future update."
            )
        )
        tools_menu.addAction(ats_action)

        cover_letter_action = QAction("Cover Letter Generator", self)
        cover_letter_action.triggered.connect(
            lambda: QMessageBox.information(
                self, "Coming Soon", "Cover letter generation is under development."
            )
        )
        tools_menu.addAction(cover_letter_action)

        # ------------------------------------------------------
        # VIEW MENU
        # ------------------------------------------------------
        view_menu = menubar.addMenu("View")

        toggle_job_panel = QAction("Show Job Description Panel", self, checkable=True)
        toggle_job_panel.setChecked(True)
        toggle_job_panel.triggered.connect(
            lambda checked: self.ui.leftPane.setVisible(checked)
        )
        view_menu.addAction(toggle_job_panel)

        toggle_output_panel = QAction(
            "Show Tailored Resume Panel", self, checkable=True
        )
        toggle_output_panel.setChecked(True)
        toggle_output_panel.triggered.connect(
            lambda checked: self.ui.rightPane.setVisible(checked)
        )
        view_menu.addAction(toggle_output_panel)

        view_menu.addSeparator()

        dark_mode_toggle = QAction("Dark Mode", self, checkable=True)
        dark_mode_toggle.setChecked(True)
        view_menu.addAction(dark_mode_toggle)

        # ------------------------------------------------------
        # HELP MENU
        # ------------------------------------------------------
        help_menu = menubar.addMenu("Help")

        help_action = QAction("User Guide", self)
        help_action.triggered.connect(
            lambda: QMessageBox.information(
                self, "Guide", "A full user guide will be included in the next update."
            )
        )
        help_menu.addAction(help_action)

        about_action = QAction("About JobFit Pro", self)
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "About JobFit Pro",
                "JobFit Pro — AI-powered resume tailoring.\nCreated by Antonio Lee Jr.",
            )
        )
        help_menu.addAction(about_action)

        # ------------------------------------------------------
        # ACCOUNT MENU (populated in window_main.py)
        # ------------------------------------------------------
        self.menu_account = menubar.addMenu("Account")

        logout_action = QAction("Sign Out", self)
        logout_action.triggered.connect(
            lambda: QMessageBox.information(
                self, "Sign Out", "Authentication system coming soon."
            )
        )
        self.menu_account.addAction(logout_action)

    # =====================================================================
    # EVENT SETUP
    # =====================================================================
    def _setup_events(self):
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnFetchJob.clicked.connect(self.fetch_job_description)
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

    # =====================================================================
    # RESUME LOADING
    # =====================================================================
    def load_resume_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Resume", "", "Documents (*.pdf *.docx)"
        )

        if path:
            self.load_resume(path)

    def load_resume(self, path):
        """Loads resume text from DOCX or PDF."""
        if path.lower().endswith(".pdf"):
            text = extract_pdf(path)
        else:
            text = extract_docx(path)

        self.state.resume_text = text
        self.state.loaded_resume_path = path
        self.ui.resumePreview.setPlainText(text)

    def load_resume_from_picker(self, path):
        if path:
            self.load_resume(path)

    # =====================================================================
    # JOB DESCRIPTION
    # =====================================================================
    def fetch_job_description(self):
        url = self.ui.inputJobURL.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Enter a job URL.")
            return

        text = fetch_job_description(url)
        if not text:
            QMessageBox.warning(self, "Error", "Could not fetch job description.")
            return

        self.state.job_text = text
        self.ui.jobPreview.setPlainText(text)

    # =====================================================================
    # TAILORING
    # =====================================================================
    def tailor_resume(self):
        if not self.state.resume_text:
            QMessageBox.warning(self, "Error", "Load a resume first.")
            return

        job_text = self.ui.jobPreview.toPlainText().strip()
        if job_text:
            self.state.job_text = job_text

        if not self.state.job_text:
            QMessageBox.warning(self, "Error", "Provide a job description.")
            return

        # Settings from panel
        settings = self.ui.settingsPanel.get_settings()  # more explicit method

        tailored = self.tailor_engine.generate(
            self.state.resume_text,
            self.state.job_text,
            limit_pages=settings.limit_pages,
            limit_one_page=settings.limit_one_page,
        )

        self.state.tailored_text = tailored
        self.ui.outputPreview.setPlainText(tailored)

        self.save_history()

    # =====================================================================
    # EXPORT
    # =====================================================================
    def export_resume(self, format_type):
        if not self.state.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        from core.exporter.pdf_exporter import export_to_pdf
        from core.exporter.docx_builder import export_to_docx

        ext = "pdf" if format_type == "pdf" else "docx"
        dialog_name = f"Export Resume ({ext.upper()})"

        path, _ = QFileDialog.getSaveFileName(
            self, dialog_name, f"Tailored_Resume.{ext}", f"*{ext}"
        )

        if not path:
            return

        if ext == "pdf":
            export_to_pdf(self.state.tailored_text, path)
        else:
            export_to_docx(self.state.tailored_text, path)

        QMessageBox.information(self, "Success", f"Exported as {ext.upper()}!")

    # =====================================================================
    # HISTORY
    # =====================================================================
    def save_history(self):
        """Builds and saves a history record using HistoryManager."""

        # Automatically extract company + role from job text
        company, role = extract_company_role(self.state.job_text)

        entry = {
            "company": company,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "job_url": self.ui.inputJobURL.text().strip(),
            "resume_url": (
                upload_resume(self.state.loaded_resume_path)
                if self.state.loaded_resume_path
                else None
            ),
        }

        self.history_manager.add_entry(entry)

    def open_history(self):
        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    # =====================================================================
    # NEW RESUME — CLEAR ALL FIELDS
    # =====================================================================
    def new_resume(self):
        confirm = QMessageBox.question(
            self,
            "Clear All?",
            "Start a new blank workspace?\nUnsaved progress will be lost.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        self.state = SessionState()
        self.ui.resumePreview.clear()
        self.ui.jobPreview.clear()
        self.ui.outputPreview.clear()
