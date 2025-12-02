"""
UI logic controller for the application
"""

import os
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

from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description
from core.exporter.docx_builder import export_to_docx
from core.processor.tailor_engine import ResumeTailor

from app.ui.tailoring_history_window import HISTORY_FILE


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        from app.ui.main_window import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # --------------------------
        # Event Bindings
        # --------------------------
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_output)
        self.ui.btnUseManualJob.clicked.connect(self.use_manual_job_description)
        self.ui.resumePicker.fileSelected.connect(self.load_resume_from_picker)

        # --------------------------
        # Internal State
        # --------------------------
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""

        self.tailor = ResumeTailor()

        # --------------------------
        # Menu Bar
        # --------------------------
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        tools_menu = QMenu("Tools", self)
        menubar.addMenu(tools_menu)

        # Tailoring History
        self.action_history = QAction("Tailoring History", self)
        tools_menu.addAction(self.action_history)
        self.action_history.triggered.connect(self.open_tailoring_history)

        # --------------------------
        # Loading Overlay (Text Only)
        # --------------------------
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

    # ============================================================
    # Loading Overlay
    # ============================================================

    def _center_loading_label(self):
        """Centers the loading overlay label."""
        width = max(320, int(self.width() * 0.4))
        height = 80
        x = self.width() // 2 - width // 2
        y = self.height() // 2 - height // 2

        self.loadingLabel.setGeometry(x, y, width, height)

    def _set_loading_visible(self, visible: bool):
        """Shows or hides the loading overlay."""
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
        """Animates the dots at the end of 'Tailoring in progress'."""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self.loadingLabel.setText(f"{self._loading_base_text}{dots}")

    # ============================================================
    # Resume Loading
    # ============================================================

    def load_resume_from_picker(self, fname: str):
        if not fname:
            return

        if fname.endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)

        self.ui.resumePreview.setPlainText(self.resume_text)

    # ============================================================
    # Fetch Job Description
    # ============================================================

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

    # ============================================================
    # Tailor Resume
    # ============================================================

    def tailor_resume(self):
        if not self.resume_text:
            QMessageBox.warning(self, "Error", "Load your resume first.")
            return

        pasted_text = self.ui.jobPreview.toPlainText().strip()
        if pasted_text:
            self.job_text = pasted_text

        if not self.job_text:
            QMessageBox.warning(self, "Error", "Paste or fetch a job description.")
            return

        # Start animated loading overlay
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
            # Hide overlay and save history entry
            self._set_loading_visible(False)
            self.save_tailoring_history()

    # ============================================================
    # Export
    # ============================================================

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

    # ============================================================
    # Manual Job Apply
    # ============================================================

    def use_manual_job_description(self):
        text = self.ui.jobPreview.toPlainText().strip()

        if not text:
            QMessageBox.warning(self, "Error", "Paste a job description first.")
            return

        self.job_text = text
        QMessageBox.information(self, "Success", "Using pasted job description.")

    # ============================================================
    # History Window
    # ============================================================

    def open_tailoring_history(self):
        from app.ui.tailoring_history_window import TailoringHistoryWindow

        self.history_window = TailoringHistoryWindow(self)
        self.history_window.show()

    # ============================================================
    # Save History Entry
    # ============================================================

    def save_tailoring_history(self):
        company = "Unknown"
        role = "Unknown"

        text = self.job_text.lower()
        if "company" in text:
            try:
                company = text.split("company")[1].split("\n")[0].strip(": .")
            except:
                pass

        # Auto-save tailored resume for history tracking
        auto_file = os.path.join(os.getcwd(), "last_tailored_resume.docx")
        export_to_docx(self.tailored_text, auto_file)

        entry = {
            "company": company,
            "role": role,
            "file": auto_file,
        }

        # Load or create history
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
            except:
                history = []
        else:
            history = []

        history.append(entry)

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    # ============================================================
    # Resize
    # ============================================================

    def resizeEvent(self, event):
        self._center_loading_label()
        super().resizeEvent(event)
