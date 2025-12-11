"""
Main Application Window Controller
----------------------------------

Controls the primary user interface and high-level workflow for JobFit Pro.

Responsibilities:
- Initialize and manage the main UI (Ui_MainWindow)
- Coordinate user actions such as loading resumes, fetching job descriptions,
  tailoring, exporting, and viewing history
- Delegate all business logic to core modules (extractor, processor, exporter,
  uploader) and centralize session data through SessionState
- Use HistoryManager for persistent storage of tailoring records

This controller focuses on orchestration and UI interaction while keeping
logic, I/O, and external service calls in dedicated modules to maintain a
clean, scalable architecture.
"""

from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtGui import QAction

# -------------------- INTERNAL APP MODULES --------------------
from app.state.session_state import SessionState
from core.history.history_manager import HistoryManager
from app.ui.tailoring_history_window import TailoringHistoryWindow, HISTORY_FILE
from app.ui.main_window_ui import Ui_MainWindow

from core.extractor.job_parser import fetch_job_description
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx

from core.processor.tailor_engine import ResumeTailor
from core.uploader.supabase_uploader import upload_resume


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ------------------------------
        # Initialize app state
        # ------------------------------
        self.state = SessionState()
        self.history_manager = HistoryManager(HISTORY_FILE)
        self.tailor_engine = ResumeTailor()

        # ------------------------------
        # Load UI
        # ------------------------------
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ------------------------------
        # Menus + Events
        # ------------------------------
        self._setup_menus()
        self._setup_events()

        # Window title
        self.setWindowTitle("JobFit Pro")

    # =====================================================================
    # MENU SETUP
    # =====================================================================
    def _setup_menus(self):
        menubar = self.menuBar()

        # ----- FILE MENU -----
        file_menu = menubar.addMenu("File")

        action_new = QAction("New Resume", self)
        action_new.triggered.connect(self.new_resume)
        file_menu.addAction(action_new)

        action_load = QAction("Load Resume", self)
        action_load.triggered.connect(self.load_resume_dialog)
        file_menu.addAction(action_load)

        file_menu.addSeparator()

        action_save_pdf = QAction("Export as PDF", self)
        action_save_pdf.triggered.connect(lambda: self.export_resume("pdf"))
        file_menu.addAction(action_save_pdf)

        action_save_docx = QAction("Export as DOCX", self)
        action_save_docx.triggered.connect(lambda: self.export_resume("docx"))
        file_menu.addAction(action_save_docx)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ----- TOOLS MENU -----
        tools_menu = menubar.addMenu("Tools")

        action_history = QAction("Tailoring History", self)
        action_history.triggered.connect(self.open_history)
        tools_menu.addAction(action_history)

    # =====================================================================
    # EVENT SETUP
    # =====================================================================
    def _setup_events(self):
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnFetchJob.clicked.connect(self.fetch_job_description)

        # File picker
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

        settings = self.ui.settingsPanel.to_dict()

        tailored = self.tailor_engine.generate(
            self.state.resume_text,
            self.state.job_text,
            limit_pages=settings.get("limit_pages", False),
            limit_one=settings.get("limit_one_page", False),
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

        if format_type == "pdf":
            from core.exporter.pdf_exporter import export_to_pdf

            ext = "pdf"
        else:
            from core.exporter.docx_builder import export_to_docx

            ext = "docx"

        path, _ = QFileDialog.getSaveFileName(
            self, f"Export Resume ({ext.upper()})", f"Tailored_Resume.{ext}", f"*{ext}"
        )

        if not path:
            return

        if format_type == "pdf":
            export_to_pdf(self.state.tailored_text, path)
        else:
            export_to_docx(self.state.tailored_text, path)

        QMessageBox.information(self, "Success", f"Exported as {ext.upper()}!")

    # =====================================================================
    # HISTORY
    # =====================================================================
    def save_history(self):
        """Builds and saves a history record using HistoryManager."""
        entry = {
            "company": "",
            "role": "",
            "timestamp": datetime.now().isoformat(),
            "resume_url": (
                upload_resume(self.state.loaded_resume_path)
                if self.state.loaded_resume_path
                else None
            ),
            "job_url": self.ui.inputJobURL.text().strip(),
        }

        self.history_manager.add_entry(entry)

    def open_history(self):
        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    # =====================================================================
    # NEW RESUME RESET
    # =====================================================================
    def new_resume(self):
        self.state = SessionState()
        self.ui.resumePreview.clear()
        self.ui.jobPreview.clear()
        self.ui.outputPreview.clear()
