# app/ui/tabs/tab_cover_letter.py
"""
Cover Letter Tab — JobFit Pro
------------------------------

Three-column layout:
  Left   — Controls (tone, length, highlight, generate button)
  Center — Formatted cover letter output + copy/export
  Right  — Live stats (word count, tone badge, keyword match bar)
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QLineEdit,
    QFrame,
    QApplication,
    QFileDialog,
    QMessageBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from core.processor.cover_letter_engine import CoverLetterWorker
from core.processor.keyword_matcher import keyword_overlap


def _word_count(text):
    return len(text.split()) if text.strip() else 0


def _section(title):
    lbl = QLabel(title)
    lbl.setStyleSheet(
        "font-size: 9pt; font-weight: 700; color: #54AED5;"
        "text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;"
    )
    return lbl


def _divider():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: #2A313C;")
    return f


TONE_COLORS = {
    "Professional": "#2563EB",
    "Friendly": "#16A34A",
    "Confident": "#9333EA",
    "Creative": "#EA580C",
}


class ToneBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.set_tone("Professional")

    def set_tone(self, tone):
        color = TONE_COLORS.get(tone, "#54AED5")
        self.setText(tone)
        self.setStyleSheet(
            f"QLabel{{background:{color}33;color:{color};border:1px solid {color};"
            f"border-radius:12px;padding:2px 14px;font-size:9pt;font-weight:700;}}"
        )


class CoverLetterTab(QWidget):
    # Emits (cover_letter_text, used_tailored_resume: bool)
    coverLetterGenerated = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resume_text = ""
        self._tailored_text = ""
        self._job_text = ""
        self._letter_text = ""
        self._used_tailored = False
        self._worker = None
        self._build_ui()

    def set_context(self, resume_text="", job_text="", tailored_text=""):
        if resume_text:
            self._resume_text = resume_text
        if tailored_text:
            self._tailored_text = tailored_text
        if job_text:
            self._job_text = job_text
        self._update_indicators()

    # ── Build ─────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)
        root.addLayout(self._build_left(), stretch=2)
        root.addLayout(self._build_center(), stretch=5)
        root.addLayout(self._build_right(), stretch=2)

    def _build_left(self):
        col = QVBoxLayout()
        col.setSpacing(10)

        title = QLabel("Cover Letter")
        title.setProperty("panelTitle", True)
        col.addWidget(title)
        col.addWidget(_divider())

        col.addWidget(_section("Source Data"))
        self.lbl_resume = QLabel("○  No resume loaded")
        self.lbl_resume.setStyleSheet("font-size: 9pt; color: #64748B;")
        self.lbl_job = QLabel("○  No job description")
        self.lbl_job.setStyleSheet("font-size: 9pt; color: #64748B;")
        col.addWidget(self.lbl_resume)
        col.addWidget(self.lbl_job)
        col.addWidget(_divider())

        col.addWidget(_section("Tone"))
        self.combo_tone = QComboBox()
        self.combo_tone.addItems(["Professional", "Friendly", "Confident", "Creative"])
        self.combo_tone.setToolTip(
            "Professional — formal and results-focused\n"
            "Friendly — warm and approachable\n"
            "Confident — assertive and direct\n"
            "Creative — distinctive and memorable"
        )
        self.combo_tone.currentTextChanged.connect(
            lambda t: self.tone_badge.set_tone(t)
        )
        col.addWidget(self.combo_tone)

        col.addWidget(_section("Length"))
        self.combo_length = QComboBox()
        self.combo_length.addItems(
            ["Short (~200w)", "Standard (~350w)", "Detailed (~500w)"]
        )
        self.combo_length.setCurrentIndex(1)
        col.addWidget(self.combo_length)

        col.addWidget(_section("Emphasize (optional)"))
        self.input_highlight = QLineEdit()
        self.input_highlight.setPlaceholderText(
            "e.g. leadership, Python, 5 yrs finance…"
        )
        self.input_highlight.setToolTip(
            "Anything specific to emphasize.\nLeave blank to let AI decide."
        )
        col.addWidget(self.input_highlight)

        col.addStretch()

        self.btn_generate = QPushButton("✉  Generate Cover Letter")
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.clicked.connect(self._generate)
        col.addWidget(self.btn_generate)

        self.btn_regenerate = QPushButton("↺  Regenerate")
        self.btn_regenerate.setFixedHeight(32)
        self.btn_regenerate.setStyleSheet(
            "QPushButton{background:#1E293B;color:#94A3B8;border:1px solid #334155;"
            "border-radius:6px;font-size:9pt;}"
            "QPushButton:hover{color:#FFFFFF;border-color:#54AED5;}"
        )
        self.btn_regenerate.clicked.connect(self._generate)
        self.btn_regenerate.hide()
        col.addWidget(self.btn_regenerate)

        return col

    def _build_center(self):
        col = QVBoxLayout()
        col.setSpacing(8)

        header = QHBoxLayout()
        lbl = QLabel("Generated Cover Letter")
        lbl.setProperty("panelTitle", True)
        header.addWidget(lbl)
        header.addStretch()

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setFixedHeight(28)
        self.btn_copy.clicked.connect(self._copy)
        self.btn_copy.hide()

        self.btn_export_docx = QPushButton("Export DOCX")
        self.btn_export_docx.setFixedHeight(28)
        self.btn_export_docx.clicked.connect(lambda: self._export("docx"))
        self.btn_export_docx.hide()

        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_pdf.setFixedHeight(28)
        self.btn_export_pdf.clicked.connect(lambda: self._export("pdf"))
        self.btn_export_pdf.hide()

        header.addWidget(self.btn_copy)
        header.addWidget(self.btn_export_docx)
        header.addWidget(self.btn_export_pdf)
        col.addLayout(header)

        self.output = QTextEdit()
        self.output.setReadOnly(False)
        self.output.setFont(QFont("Calibri", 11))
        self.output.setPlaceholderText(
            "Your cover letter will appear here after generation…\n\n"
            "Make sure a resume and job description are loaded on the Tailor tab first."
        )
        self.output.textChanged.connect(self._on_text_changed)
        col.addWidget(self.output)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar{border:none;background:#1E293B;border-radius:2px;}"
            "QProgressBar::chunk{background:#54AED5;border-radius:2px;}"
        )
        self.progress.hide()
        col.addWidget(self.progress)

        return col

    def _build_right(self):
        col = QVBoxLayout()
        col.setSpacing(10)

        col.addWidget(_section("Tone"))
        self.tone_badge = ToneBadge()
        col.addWidget(self.tone_badge)

        col.addWidget(_divider())
        col.addWidget(_section("Word Count"))
        self.lbl_word_count = QLabel("—")
        self.lbl_word_count.setStyleSheet(
            "font-size:22pt;font-weight:700;color:#FFFFFF;"
        )
        self.lbl_word_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.lbl_word_count)
        self.lbl_word_target = QLabel("")
        self.lbl_word_target.setStyleSheet("font-size:8pt;color:#64748B;")
        self.lbl_word_target.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.lbl_word_target)

        col.addWidget(_divider())
        col.addWidget(_section("Keyword Coverage"))
        self.lbl_kw_score = QLabel("—")
        self.lbl_kw_score.setStyleSheet("font-size:22pt;font-weight:700;color:#FFFFFF;")
        self.lbl_kw_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.lbl_kw_score)
        self.kw_bar = QProgressBar()
        self.kw_bar.setRange(0, 100)
        self.kw_bar.setValue(0)
        self.kw_bar.setFixedHeight(8)
        self.kw_bar.setTextVisible(False)
        self.kw_bar.setStyleSheet(
            "QProgressBar{border:none;background:#1E293B;border-radius:4px;}"
            "QProgressBar::chunk{background:#54AED5;border-radius:4px;}"
        )
        col.addWidget(self.kw_bar)
        hint = QLabel("keyword match vs job description")
        hint.setStyleSheet("font-size:8pt;color:#475569;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        col.addWidget(hint)

        col.addWidget(_divider())
        col.addWidget(_section("Tips"))
        tips = QLabel(
            "• Keep it to one page\n"
            "• Mirror keywords from the job post\n"
            "• Lead with your strongest win\n"
            "• Name the company specifically\n"
            "• End with a clear call to action"
        )
        tips.setStyleSheet("font-size:8pt;color:#64748B;line-height:1.8;")
        tips.setWordWrap(True)
        col.addWidget(tips)
        col.addStretch()
        return col

    # ── Logic ─────────────────────────────────────────────────
    def _update_indicators(self):
        if self._tailored_text:
            self.lbl_resume.setText("●  Using tailored resume")
            self.lbl_resume.setStyleSheet("font-size:9pt;color:#34D399;")
        elif self._resume_text:
            self.lbl_resume.setText("●  Using original resume")
            self.lbl_resume.setStyleSheet("font-size:9pt;color:#FBBF24;")
        else:
            self.lbl_resume.setText("○  No resume loaded")
            self.lbl_resume.setStyleSheet("font-size:9pt;color:#64748B;")

        if self._job_text:
            self.lbl_job.setText("●  Job description ready")
            self.lbl_job.setStyleSheet("font-size:9pt;color:#34D399;")
        else:
            self.lbl_job.setText("○  No job description")
            self.lbl_job.setStyleSheet("font-size:9pt;color:#64748B;")

    def _on_text_changed(self):
        text = self.output.toPlainText()
        wc = _word_count(text)
        self.lbl_word_count.setText(str(wc) if wc else "—")

        key = self.combo_length.currentText().split()[0]
        targets = {"Short": (150, 250), "Standard": (300, 400), "Detailed": (450, 560)}
        lo, hi = targets.get(key, (300, 400))
        self.lbl_word_target.setText(f"target {lo}–{hi} words")
        if wc:
            color = "#34D399" if lo <= wc <= hi else "#F87171" if wc < lo else "#FBBF24"
            self.lbl_word_count.setStyleSheet(
                f"font-size:22pt;font-weight:700;color:{color};"
            )

        if text and self._job_text:
            score = int(keyword_overlap(self._job_text, text)["match_rate"])
            self.lbl_kw_score.setText(f"{score}%")
            self.kw_bar.setValue(score)
            kc = "#34D399" if score >= 60 else "#FBBF24" if score >= 35 else "#F87171"
            self.lbl_kw_score.setStyleSheet(
                f"font-size:22pt;font-weight:700;color:{kc};"
            )
            self.kw_bar.setStyleSheet(
                f"QProgressBar{{border:none;background:#1E293B;border-radius:4px;}}"
                f"QProgressBar::chunk{{background:{kc};border-radius:4px;}}"
            )

    def _generate(self):
        # Prefer tailored resume — it's already keyword-optimized for this job.
        # Fall back to original if tailoring hasn't been run yet.
        source_resume = self._tailored_text or self._resume_text

        if not source_resume:
            QMessageBox.warning(
                self,
                "Missing Resume",
                "Load a resume on the Tailor tab first.\n\n"
                "Tip: Tailor your resume first for the best cover letter results.",
            )
            return
        if not self._job_text:
            QMessageBox.warning(
                self,
                "Missing Job Description",
                "Paste or fetch a job description on the Tailor tab first.",
            )
            return

        tone = self.combo_tone.currentText()
        length = self.combo_length.currentText().split()[0]
        highlight = self.input_highlight.text().strip()

        self.tone_badge.set_tone(tone)
        self.btn_generate.setEnabled(False)
        self.btn_regenerate.setEnabled(False)
        self.btn_generate.setText("Generating…")
        self.progress.show()

        self._worker = CoverLetterWorker(
            source_resume, self._job_text, tone, length, highlight
        )
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, text):
        self._letter_text = text
        self._used_tailored = bool(self._tailored_text)
        self.output.setPlainText(text)
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.output.setTextCursor(cursor)

        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("✉  Generate Cover Letter")
        self.btn_regenerate.setEnabled(True)
        self.btn_regenerate.show()
        self.progress.hide()
        self.btn_copy.show()
        self.btn_export_docx.show()
        self.btn_export_pdf.show()

        # Notify window_main so it can save to history if applicable
        self.coverLetterGenerated.emit(text, self._used_tailored)

    def _on_error(self, msg):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("✉  Generate Cover Letter")
        self.btn_regenerate.setEnabled(True)
        self.progress.hide()
        QMessageBox.critical(
            self, "Generation Failed", f"Could not generate cover letter:\n\n{msg}"
        )

    def _copy(self):
        text = self.output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btn_copy.setText("Copied!")
            QTimer.singleShot(1500, lambda: self.btn_copy.setText("Copy"))

    def _export(self, fmt):
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.warning(
                self, "Nothing to Export", "Generate a cover letter first."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save Cover Letter ({fmt.upper()})",
            f"Cover_Letter.{fmt}",
            f"*.{fmt}",
        )
        if not path:
            return
        try:
            if fmt == "docx":
                from core.exporter.docx_builder import export_to_docx

                export_to_docx(text, path)
            else:
                from core.exporter.pdf_exporter import export_to_pdf

                export_to_pdf(text, path)
            QMessageBox.information(
                self, "Exported", f"Cover letter saved as {fmt.upper()}!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
