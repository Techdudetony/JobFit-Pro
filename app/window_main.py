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

v2 CHANGES:
- Keyboard shortcuts added (Ctrl+T, Ctrl+F, Ctrl+M, Ctrl+E, Ctrl+Shift+E,
  Ctrl+H, Ctrl+N, Ctrl+O, Ctrl+Q, Ctrl+Shift+T)
- Light/Dark mode toggle added to View menu
- Theme menu label updates dynamically after each toggle
- _setup_shortcuts() added as a dedicated method
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
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QShortcut

from app.ui.toast_notification import ToastNotification
from app.ui.dialogs.tailor_context_dialog import TailorContextDialog
from core.processor.context_question_engine import ContextQuestionWorker
from services.sync_manager import sync_manager

# ---------------- CORE LOGIC MODULES ----------------
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description

from core.uploader.supabase_uploader import upload_resume
from core.exporter.docx_builder import export_to_docx
from core.exporter.resume_style_engine import ResumeStyleEngine
from core.exporter.pdf_exporter import export_to_pdf
from core.processor.tailor_engine import ResumeTailor
from core.processor.keyword_matcher import keyword_overlap
from core.processor.job_meta_extractor import JobMetaWorker

LAST_RESUME_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "last_resume.json"
)

# Local folder where per-tailoring PDFs are saved
HISTORY_RESUMES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "data", "history_resumes"
)

# ---------------- AUTH SYSTEM -----------------------
from services.auth_manager import auth
from app.ui.auth_modal import AuthModal
from app.ui.onboarding import OnboardingManager, has_completed_onboarding, reset_onboarding

# ---------------- HISTORY --------------------------
from app.ui.tailoring_history_window import HISTORY_FILE


# ==============================================================================
# Background Worker
# ==============================================================================
class TailorWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, tailor, resume_text, job_text, settings, context=""):
        super().__init__()
        self.tailor      = tailor
        self.resume_text = resume_text
        self.job_text    = job_text
        self.settings    = settings
        self.context     = context

    def run(self):
        try:
            result = self.tailor.generate(
                self.resume_text,
                self.job_text,
                limit_pages=self.settings.get("limit_pages", False),
                limit_one=self.settings.get("limit_one", False),
                context=self.context,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ==============================================================================
# Main Window
# ==============================================================================
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

            if result != QDialog.DialogCode.Accepted:
                return

            self.user = self.auth.get_user()

        if not self.user:
            print("AUTH FAILED: No valid Supabase session returned.")
            return

        self.auth_ok = True
        print("MainWindow created, user:", self.user.email if self.user else None)

        # ============================================================
        # 2. LOAD UI FROM PURE LAYOUT CLASS
        # ============================================================
        from app.ui.main_window import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ============================================================
        # 3. LOADING OVERLAY SETUP
        # ============================================================
        self._loading_base_text = "Tailoring in progress"
        self._loading_dots = 0

        self.loadingLabel = QLabel(self)
        self.loadingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loadingLabel.setStyleSheet("""
            QLabel {
                background-color: rgba(15, 23, 42, 220);
                color: #E5E7EB;
                font-size: 16pt;
                font-weight: 600;
                border-radius: 16px;
                padding: 24px 40px;
                min-width: 400px;
            }
        """)
        self.loadingLabel.hide()

        self.loadingTimer = QTimer(self)
        self.loadingTimer.setInterval(400)
        self.loadingTimer.timeout.connect(self._update_loading_text)

        self._center_loading_label()

        # ============================================================
        # 4. INTERNAL STATE
        # ============================================================
        self.resume_text   = ""
        self.job_text      = ""
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
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

        # Last used resume button
        self.ui.btnLastResume.clicked.connect(self.load_last_resume)
        self._refresh_last_resume_button()

        # ============================================================
        # 6. MENU BAR SETUP
        # ============================================================
        self._setup_menus()

        # ============================================================
        # 7. KEYBOARD SHORTCUTS  ← NEW in v2
        # ============================================================
        self._setup_shortcuts()

        # ============================================================
        # 8. ONBOARDING TUTORIAL
        # ============================================================
        self.onboarding = OnboardingManager(self)
        # Slight delay so the window fully renders before overlay appears
        QTimer.singleShot(400, self.onboarding.start)

        # ============================================================
        # 9. WIRE ATS PANEL → HISTORY TAB
        # ============================================================
        # Give the History tab a reference to the ATS panel so "View ATS"
        # buttons can replay stored analyses without any extra API calls.
        if hasattr(self.ui, "tabHistory") and hasattr(self.ui, "atsPanel"):
            self.ui.tabHistory.set_ats_panel(self.ui.atsPanel)

        # ============================================================
        # 10. WIRE COVER LETTER → HISTORY
        # ============================================================
        if hasattr(self.ui, "tabCoverLetter"):
            self.ui.tabCoverLetter.coverLetterGenerated.connect(
                self._on_cover_letter_generated
            )

        # ============================================================
        # 11. WIRE ATS analysisReady → TOAST + BADGE
        # ============================================================
        if hasattr(self.ui, "atsPanel"):
            self.ui.atsPanel.analysisReady.connect(self._on_ats_ready)

        # ============================================================
        # 12. SYNC ON LOGIN — pull cloud history + prefs
        # ============================================================
        # Small delay so the window is fully visible before network calls fire
        QTimer.singleShot(1500, self._sync_on_login)

    # ==================================================================
    # MENU BAR  ← UPDATED in v2 (added View menu with theme toggle)
    # ==================================================================
    def _setup_menus(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # ---- Tools menu ----
        tools_menu = QMenu("Tools", self)
        menubar.addMenu(tools_menu)

        action_hist = QAction("Tailoring History", self)
        action_hist.setShortcut(QKeySequence("Ctrl+H"))
        tools_menu.addAction(action_hist)
        action_hist.triggered.connect(self.open_tailoring_history)

        action_ats = QAction("View ATS Breakdown", self)
        action_ats.setShortcut(QKeySequence("Ctrl+Shift+A"))
        action_ats.triggered.connect(lambda: self.ui.atsPanel.toggle())
        tools_menu.addAction(action_ats)

        # ---- File menu ----
        file_menu = QMenu("File", self)
        menubar.addMenu(file_menu)

        action_new = QAction("New Resume", self)
        action_new.setShortcut(QKeySequence("Ctrl+N"))
        action_new.triggered.connect(self.new_resume)
        file_menu.addAction(action_new)

        action_load = QAction("Load Resume", self)
        action_load.setShortcut(QKeySequence("Ctrl+O"))
        action_load.triggered.connect(self._open_resume_dialog)
        file_menu.addAction(action_load)

        file_menu.addSeparator()

        action_export_docx = QAction("Export as DOCX", self)
        action_export_docx.setShortcut(QKeySequence("Ctrl+E"))
        action_export_docx.triggered.connect(self.export_docx_output)
        file_menu.addAction(action_export_docx)

        action_export_pdf = QAction("Export as PDF", self)
        action_export_pdf.setShortcut(QKeySequence("Ctrl+Shift+E"))
        action_export_pdf.triggered.connect(self.export_pdf_output)
        file_menu.addAction(action_export_pdf)

        file_menu.addSeparator()

        action_quit = QAction("Exit", self)
        action_quit.setShortcut(QKeySequence("Ctrl+Q"))
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)

        # ---- View menu (NEW in v2) ----
        view_menu = QMenu("View", self)
        menubar.addMenu(view_menu)

        self.theme_action = QAction(self._theme_label(), self, checkable=True)
        self.theme_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.theme_action.triggered.connect(self.toggle_theme)
        # Reflect current theme state
        try:
            import services.theme_manager as tm_module
            self.theme_action.setChecked(
                tm_module.theme_manager.is_dark_mode()
                if tm_module.theme_manager else True
            )
        except Exception:
            self.theme_action.setChecked(True)
        view_menu.addAction(self.theme_action)

        # ---- Help menu ----
        help_menu = QMenu("Help", self)
        menubar.addMenu(help_menu)

        action_tutorial = QAction("Show Tutorial", self)
        action_tutorial.triggered.connect(lambda: self.onboarding.start(force=True))
        help_menu.addAction(action_tutorial)

        help_menu.addSeparator()

        action_about = QAction("About JobFit Pro", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)

        # ---- Account menu (right-aligned) ----
        self._setup_user_menu(menubar)

    def _show_about(self):
        QMessageBox.information(
            self,
            "About JobFit Pro",
            "JobFit Pro — AI-powered resume tailoring.\nCreated by Antonio Lee Jr.",
        )

    # ==================================================================
    # USER MENU (TOP RIGHT)
    # ==================================================================
    def _setup_user_menu(self, menubar: QMenuBar) -> None:
        # Spacer to push account menu right
        spacer = menubar.addMenu(" " * 200)
        spacer.setDisabled(True)

        email = getattr(self.user, "email", "Account")
        account_menu = menubar.addMenu(email)

        logout_action = QAction("Sign Out", self)
        logout_action.triggered.connect(self._sign_out)
        account_menu.addAction(logout_action)

    def _sign_out(self) -> None:
        self.auth.sign_out()
        QMessageBox.information(self, "Signed Out", "You have been signed out.")
        QApplication.instance().quit()

    # ==================================================================
    # KEYBOARD SHORTCUTS  ← NEW in v2
    # ==================================================================
    def _setup_shortcuts(self):
        """
        Shortcuts for actions that don't live in a menu action.
        Menu-bound shortcuts (Ctrl+H, Ctrl+N, Ctrl+O, Ctrl+E,
        Ctrl+Shift+E, Ctrl+Q, Ctrl+Shift+T) are already set via
        QAction.setShortcut() above.
        """
        # Tailor Resume — the primary action
        self._sc_tailor = QShortcut(QKeySequence("Ctrl+T"), self)
        self._sc_tailor.activated.connect(self.ui.btnTailor.click)

        # Fetch job description from URL
        self._sc_fetch = QShortcut(QKeySequence("Ctrl+F"), self)
        self._sc_fetch.activated.connect(self.ui.btnFetchJob.click)

        # Use manually pasted job description
        self._sc_manual = QShortcut(QKeySequence("Ctrl+M"), self)
        self._sc_manual.activated.connect(self.ui.btnUseManualJob.click)

    # ==================================================================
    # THEME TOGGLE  ← NEW in v2
    # ==================================================================
    def _theme_label(self) -> str:
        """Returns the right menu label for the current theme."""
        try:
            import services.theme_manager as tm_module
            if tm_module.theme_manager and tm_module.theme_manager.is_dark_mode():
                return "Switch to Light Mode"
        except Exception:
            pass
        return "Switch to Dark Mode"

    def toggle_theme(self):
        """Toggle light/dark and update menu label + checkmark."""
        try:
            import services.theme_manager as tm_module
            if tm_module.theme_manager:
                tm_module.theme_manager.toggle_theme()
                is_dark = tm_module.theme_manager.is_dark_mode()
                self.theme_action.setChecked(is_dark)
                self.theme_action.setText(self._theme_label())

                # Push updated theme preference to Supabase
                self._push_current_prefs()
        except Exception as e:
            print(f"[THEME] Toggle failed: {e}")

    # ==================================================================
    # LOADING OVERLAY HELPERS
    # ==================================================================
    def _center_loading_label(self):
        if not hasattr(self, "loadingLabel"):
            return
        if not hasattr(self, "ui") or not hasattr(self.ui, "central_widget"):
            return
        parent = self.ui.central_widget
        w = max(420, int(parent.width() * 0.5))
        h = 80
        x = (parent.width() - w) // 2
        y = (parent.height() - h) // 2
        self.loadingLabel.setGeometry(x, y, w, h)

    def _set_loading_visible(self, visible: bool):
        if visible:
            self._loading_dots = 0
            self._update_loading_text()
            self._center_loading_label()
            self.loadingLabel.show()
            self.loadingLabel.raise_()
            self.loadingTimer.start()
            QApplication.processEvents()
        else:
            self.loadingTimer.stop()
            self.loadingLabel.hide()

    def _update_loading_text(self):
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
        self._save_last_resume(fname)
        self._refresh_last_resume_button()
        # Keep cover letter tab in sync
        if hasattr(self.ui, "tabCoverLetter"):
            self.ui.tabCoverLetter.set_context(resume_text=self.resume_text)

    def _save_last_resume(self, path: str):
        """Persist the last used resume path."""
        try:
            with open(LAST_RESUME_FILE, "w", encoding="utf-8") as f:
                json.dump({"path": path}, f)
        except Exception as e:
            print(f"[LAST RESUME] Save failed: {e}")

    def _load_last_resume_path(self) -> str:
        """Return last used resume path if it still exists on disk."""
        try:
            if os.path.exists(LAST_RESUME_FILE):
                with open(LAST_RESUME_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                path = data.get("path", "")
                if os.path.exists(path):
                    return path
        except Exception:
            pass
        return ""

    def _refresh_last_resume_button(self):
        """Show the Last Resume button only when a valid saved path exists."""
        path = self._load_last_resume_path()
        if path:
            name = os.path.basename(path)
            self.ui.btnLastResume.setText(f"↩ Last: {name}")
            self.ui.btnLastResume.setToolTip(f"Reload: {path}")
            self.ui.btnLastResume.setVisible(True)
        else:
            self.ui.btnLastResume.setVisible(False)

    def load_last_resume(self):
        """Load the previously used resume."""
        path = self._load_last_resume_path()
        if not path:
            QMessageBox.information(self, "No Last Resume", "No previously used resume found.")
            return
        self.ui.resumePicker.setPath(path)
        self.load_resume_from_picker(path)

    def _open_resume_dialog(self):
        """Open file dialog to load a resume (triggered via menu/shortcut)."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Resume", "", "Documents (*.pdf *.docx)"
        )
        if path:
            self.ui.resumePicker.setPath(path)
            self.load_resume_from_picker(path)

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
        if hasattr(self.ui, "tabCoverLetter"):
            self.ui.tabCoverLetter.set_context(job_text=self.job_text)

    # ==================================================================
    # MANUAL JOB DESCRIPTION
    # ==================================================================
    def use_manual_job_description(self):
        txt = self.ui.jobPreview.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "Error", "Paste a job description first.")
            return
        self.job_text = txt
        if hasattr(self.ui, "tabCoverLetter"):
            self.ui.tabCoverLetter.set_context(job_text=self.job_text)
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ==================================================================
    # TAILORING LOGIC
    # ==================================================================
    def tailor_resume(self):
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        pasted = self.ui.jobPreview.toPlainText().strip()
        if pasted:
            self.job_text = pasted

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Paste or fetch a job description.")
            return

        # Disable button while generating questions
        self.ui.btnTailor.setEnabled(False)

        # Show toast while OpenAI generates personalized questions
        toast = ToastNotification(
            "Personalizing your questions...", parent=self, style="info", duration=6000
        )
        toast.show_toast()

        # Fire async question generation
        self._question_worker = ContextQuestionWorker(
            self.resume_text, self.job_text
        )
        self._question_worker.finished.connect(self._on_questions_ready)
        self._question_worker.start()

    def _on_questions_ready(self, questions: list):
        """Called when OpenAI returns personalized questions — show dialog."""
        self.ui.btnTailor.setEnabled(True)

        dialog = TailorContextDialog(questions, parent=self)
        result = dialog.exec()

        if result != QDialog.DialogCode.Accepted:
            return  # User dismissed — do nothing

        context  = dialog.get_context()
        settings = self.ui.settingsPanel.to_dict()

        self._set_loading_visible(True)
        self.ui.btnTailor.setEnabled(False)

        self.worker = TailorWorker(
            self.tailor, self.resume_text, self.job_text, settings, context=context
        )
        self.worker.finished.connect(self._on_tailor_done)
        self.worker.error.connect(self._on_tailor_error)
        self.worker.start()

    def _on_tailor_done(self, result: str):
        self.tailored_text = result
        self.ui.outputPreview.setPlainText(self.tailored_text)

        # Quick heuristic ATS score bar (instant, no API call).
        ats_result = keyword_overlap(self.job_text, self.tailored_text)
        self.ui.outputPanel.setScore(int(ats_result["match_rate"]))

        self._set_loading_visible(False)
        self.ui.btnTailor.setEnabled(True)

        # Keep cover letter tab in sync with the freshly tailored resume
        if hasattr(self.ui, "tabCoverLetter"):
            self.ui.tabCoverLetter.set_context(tailored_text=self.tailored_text)

        # Save PDF locally first (guaranteed), then kick off meta extraction + Supabase async
        if self.tailored_text:
            self._pending_history_entry = self._save_pdf_and_build_entry()
            self._start_meta_extraction()

        # Fire ATS analysis AFTER UI is responsive — 200ms delay so the
        # user sees the tailored resume before any processing begins.
        QTimer.singleShot(200, self._start_ats_analysis)

    def _start_ats_analysis(self):
        """
        Kick off ATS analysis in the background.
        The panel opens and populates itself; when done it emits analysisReady
        which triggers the toast + sidebar badge.
        """
        self.ui.atsPanel.load(self.job_text, self.tailored_text)

    def _save_pdf_and_build_entry(self) -> dict:
        """Save tailored resume as local PDF, return a partial history entry."""
        import uuid
        os.makedirs(HISTORY_RESUMES_DIR, exist_ok=True)

        filename  = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
        local_pdf = os.path.join(HISTORY_RESUMES_DIR, filename)

        try:
            export_to_pdf(self.tailored_text, local_pdf)
        except Exception as e:
            print(f"[HISTORY] PDF save failed: {e}")
            local_pdf = ""

        return {
            "company":    "Unknown",          # filled in by meta worker
            "role":       "Unknown",          # filled in by meta worker
            "job_url":    self.ui.inputJobURL.text().strip(),
            "resume_url": local_pdf,          # local path; overwritten if Supabase succeeds
            "local_pdf":  local_pdf,          # always kept as fallback
            "timestamp":  datetime.now().isoformat(),
            "ats_result": None,               # filled in when keyword_analyzer finishes
        }

    def _start_meta_extraction(self):
        """Use OpenAI to extract company + role from job text in background."""
        self._meta_worker = JobMetaWorker(self.job_text)
        self._meta_worker.finished.connect(self._on_meta_done)
        self._meta_worker.start()

    def _on_meta_done(self, meta: dict):
        """Called when OpenAI returns company + role. Finalizes and writes history."""
        if not hasattr(self, "_pending_history_entry"):
            return

        entry = self._pending_history_entry
        entry["company"] = meta.get("company", "Unknown")
        entry["role"]    = meta.get("role",    "Unknown")

        # Try Supabase upload (non-blocking — if it fails, local_pdf is the fallback)
        local_pdf = entry.get("local_pdf", "")
        if local_pdf and os.path.exists(local_pdf):
            try:
                url = upload_resume(local_pdf)
                if url:
                    entry["resume_url"] = url
            except Exception as e:
                print(f"[HISTORY] Supabase upload failed, keeping local path: {e}")

        # Write entry now WITHOUT ats_result — it will be patched in by _on_ats_ready
        # once the background analysis finishes (which fires separately after tailor)
        self._write_history_entry(entry)
        del self._pending_history_entry

    def _write_history_entry(self, entry: dict):
        """Append entry to local history JSON, then push to Supabase async."""
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

        # Push to Supabase in background — failure is silent, local copy is the source of truth
        sync_manager.push_history_entry(
            entry,
            on_done=lambda row_id: print(f"[SYNC] History pushed: {row_id}"),
            on_error=lambda e: print(f"[SYNC] History push failed (local saved): {e}"),
        )

    def _on_tailor_error(self, error_msg: str):
        self._set_loading_visible(False)
        self.ui.btnTailor.setEnabled(True)
        QMessageBox.critical(self, "Tailoring Failed", error_msg)

    # ==================================================================
    # EXPORT: DOCX
    # ==================================================================
    def export_docx_output(self):
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Tailored Resume", "Tailored_Resume.docx",
            "Word Document (*.docx)",
        )
        if not path:
            return

        # Use selected style from Settings tab if available
        style = "prestige"
        if hasattr(self.ui, "tabSettings"):
            try:
                style = self.ui.tabSettings.get_selected_style()
            except Exception:
                pass

        try:
            engine = ResumeStyleEngine()
            engine.export(self.tailored_text, style=style, output_path=path)
            QMessageBox.information(
                self, "Exported",
                f"Resume exported successfully!\nStyle: {style.replace('_', ' ').title()}"
            )
        except Exception as e:
            print(f"[EXPORT] Style engine failed, falling back: {e}")
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
            self, "Save Tailored Resume", "Tailored_Resume.pdf",
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        style = "prestige"
        if hasattr(self.ui, "tabSettings"):
            try:
                style = self.ui.tabSettings.get_selected_style()
            except Exception:
                pass

        try:
            import tempfile, os
            from docx2pdf import convert
            engine = ResumeStyleEngine()
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp_path = tmp.name
            engine.export(self.tailored_text, style=style, output_path=tmp_path)
            convert(tmp_path, path)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            QMessageBox.information(
                self, "Exported",
                f"PDF exported successfully!\nStyle: {style.replace('_', ' ').title()}"
            )
        except Exception as e:
            print(f"[EXPORT] Style PDF failed, falling back: {e}")
            export_to_pdf(self.tailored_text, path)
            QMessageBox.information(self, "Success", "PDF exported successfully!")

    # ==================================================================
    # HISTORY WINDOW
    # ==================================================================
    def open_tailoring_history(self):
        """Switch to the History tab (replaces old dialog)."""
        self.ui.sidebarNav.set_tab(1)

    # ==================================================================
    # NEW RESUME — CLEAR ALL FIELDS
    # ==================================================================
    def new_resume(self):
        confirm = QMessageBox.question(
            self,
            "Clear All?",
            "Start a new blank workspace?\nUnsaved progress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.resume_text   = ""
        self.job_text      = ""
        self.tailored_text = ""
        self.ui.resumePreview.clear()
        self.ui.jobPreview.clear()
        self.ui.outputPreview.clear()

    # ==================================================================
    # ATS ANALYSIS READY → TOAST + SIDEBAR BADGE
    # ==================================================================
    def _on_ats_ready(self, score: int):
        """
        Fires when the OpenAI ATS analysis finishes in the background.
        1. Shows a toast notification
        2. Lights up the Tailor tab badge
        3. Patches ats_result into the latest history entry (local + Supabase)
        """
        # Pick toast style based on score
        if score >= 75:
            style, emoji = "success", "✅"
        elif score >= 50:
            style, emoji = "warning", "⚠️"
        else:
            style, emoji = "error", "❌"

        msg = f"{emoji} ATS Analysis ready — {score}% match"
        toast = ToastNotification(msg, parent=self, style=style, duration=5000)
        toast.show_toast()

        # Light up badge on Tailor tab (index 0)
        if hasattr(self.ui, "sidebarNav"):
            self.ui.sidebarNav.set_badge(0, True)

        # Patch ats_result into the most recent history entry
        ats_result = getattr(self.ui.atsPanel, "_last_analysis", None)
        if not ats_result:
            return

        try:
            if not os.path.exists(HISTORY_FILE):
                return
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            if not history:
                return

            history[-1]["ats_result"]   = ats_result
            history[-1]["last_updated"] = datetime.now().isoformat()

            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)

            print("[HISTORY] ATS result patched into latest entry.")

            # Refresh history tab so the View ATS button appears immediately
            if hasattr(self.ui, "tabHistory"):
                self.ui.tabHistory.load_history()

            # Push updated entry to Supabase
            sync_manager.push_history_entry(
                history[-1],
                on_done=lambda _: print("[SYNC] ATS-patched entry pushed."),
                on_error=lambda e: print(f"[SYNC] ATS patch push failed: {e}"),
            )

        except Exception as e:
            print(f"[HISTORY] Failed to patch ATS result: {e}")

    # ==================================================================
    # COVER LETTER → HISTORY SAVE
    # ==================================================================
    def _on_cover_letter_generated(self, letter_text: str, used_tailored: bool):
        """
        If the cover letter was built from the tailored resume, patch it
        into the most recent history entry so it's permanently linked.
        Only saves if a history entry already exists for this session.
        """
        if not used_tailored:
            return  # Generated from original resume — not tied to a history entry

        if not os.path.exists(HISTORY_FILE):
            return

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            return

        if not history:
            return

        # Patch the most recent entry
        history[-1]["cover_letter"] = letter_text
        history[-1]["last_updated"] = datetime.now().isoformat()

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

        print("[HISTORY] Cover letter saved to latest history entry.")

        # Push updated entry to Supabase
        sync_manager.push_history_entry(
            history[-1],
            on_done=lambda _: print("[SYNC] Cover letter entry pushed."),
            on_error=lambda e: print(f"[SYNC] Cover letter push failed: {e}"),
        )

    # ==================================================================
    # SYNC — LOGIN PULL
    # ==================================================================
    def _sync_on_login(self):
        """Pull preferences then history from Supabase after login."""
        print("[SYNC] Starting login sync...")

        # Pull preferences first
        sync_manager.pull_preferences(
            on_done=self._on_prefs_pulled,
            on_error=lambda e: print(f"[SYNC] Prefs pull failed: {e}"),
        )

        # Pull history in parallel
        local_history = self._read_local_history()
        sync_manager.pull_and_merge_history(
            local_history,
            on_done=self._on_history_pulled,
            on_error=lambda e: print(f"[SYNC] History pull failed: {e}"),
        )

    def _on_prefs_pulled(self, prefs: dict):
        """Apply pulled preferences — theme and settings panel state."""
        if not prefs:
            # No cloud prefs yet — push current local state up
            self._push_current_prefs()
            return

        import services.theme_manager as tm_module

        # Apply theme if different from current
        cloud_theme = prefs.get("theme", "dark")
        if tm_module.theme_manager and cloud_theme != tm_module.theme_manager.current_theme:
            tm_module.theme_manager.apply_theme(cloud_theme)
            print(f"[SYNC] Applied cloud theme: {cloud_theme}")

        # Apply settings panel checkboxes (Tailor tab)
        cloud_settings = prefs.get("settings", {})
        if cloud_settings and hasattr(self.ui, "settingsPanel"):
            sp = self.ui.settingsPanel
            if "focus_keywords" in cloud_settings:
                sp.chk_focus_keywords.setChecked(cloud_settings["focus_keywords"])
            if "keep_length" in cloud_settings:
                sp.chk_keep_length.setChecked(cloud_settings["keep_length"])
            if "limit_pages" in cloud_settings:
                sp.chk_limit_pages.setChecked(cloud_settings["limit_pages"])
            if "limit_one" in cloud_settings:
                sp.chk_limit_one.setChecked(cloud_settings["limit_one"])
            if "ats_friendly" in cloud_settings:
                sp.chk_ats_friendly.setChecked(cloud_settings["ats_friendly"])

        # Mirror the same values into the Settings tab checkboxes
        if cloud_settings and hasattr(self.ui, "tabSettings"):
            ts = self.ui.tabSettings
            try:
                ts.chk_default_keywords.setChecked(cloud_settings.get("focus_keywords", False))
                ts.chk_default_ats.setChecked(cloud_settings.get("ats_friendly", True))
                ts.chk_default_keep_len.setChecked(cloud_settings.get("keep_length", False))
                ts.chk_default_one_page.setChecked(cloud_settings.get("limit_one", False))
            except Exception as e:
                print(f"[SYNC] Failed to mirror prefs to Settings tab: {e}")

        # Update Settings tab theme button label + restore style
        if hasattr(self.ui, "tabSettings"):
            try:
                import services.theme_manager as tm_module
                if tm_module.theme_manager:
                    is_dark = tm_module.theme_manager.is_dark_mode()
                    self.ui.tabSettings.btn_toggle_theme.setText(
                        "Switch to Light Mode" if is_dark else "Switch to Dark Mode"
                    )
                # Restore resume style from cloud prefs if present
                cloud_style = cloud_settings.get("resume_style")
                if cloud_style:
                    self.ui.tabSettings.style_picker.set_selected(cloud_style)
            except Exception:
                pass

        print("[SYNC] Preferences applied from cloud.")

    def _on_history_pulled(self, merged: list):
        """Save merged history to local JSON and refresh the history tab."""
        if not merged:
            return

        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=4)
            print(f"[SYNC] History merged: {len(merged)} entries saved locally.")

            # Refresh the history tab if it's loaded
            if hasattr(self.ui, "tabHistory"):
                self.ui.tabHistory.load_history()

        except Exception as e:
            print(f"[SYNC] Failed to save merged history: {e}")

    def _read_local_history(self) -> list:
        """Read local history JSON, return empty list on any error."""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _push_current_prefs(self):
        """Push current local theme + settings to Supabase."""
        import services.theme_manager as tm_module
        theme = "dark"
        if tm_module.theme_manager:
            theme = "dark" if tm_module.theme_manager.is_dark_mode() else "light"

        settings = {}
        if hasattr(self.ui, "settingsPanel"):
            settings = self.ui.settingsPanel.to_dict()

        sync_manager.push_preferences(theme, settings)

    # ==================================================================
    # WINDOW RESIZE → RECENTER OVERLAY
    # ==================================================================
    def resizeEvent(self, event):
        self._center_loading_label()
        super().resizeEvent(event)