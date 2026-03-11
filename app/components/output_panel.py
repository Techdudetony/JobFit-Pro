"""
OutputPanel
----------------------------------------------

Displays a beautifully formatted preview of the tailored resume with:
- Styled headers and sections
- Proper spacing and typography
- Read-only formatted view
- Copy-to-clipboard functionality
- ATS match score bar
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QApplication,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor


class OutputPanel(QWidget):

    def __init__(self, title: str = "Tailored Resume", parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # -----------------------------------------------------------
        # HEADER ROW
        # -----------------------------------------------------------
        header_layout = QHBoxLayout()

        label = QLabel(title, self)
        label.setProperty("panelTitle", True)
        header_layout.addWidget(label)
        header_layout.addStretch()

        self.btnCopy = QPushButton("Copy", self)
        self.btnCopy.setProperty("panelButton", True)
        header_layout.addWidget(self.btnCopy)

        main_layout.addLayout(header_layout)

        # -----------------------------------------------------------
        # ATS SCORE ROW
        # -----------------------------------------------------------
        score_row = QHBoxLayout()
        self.score_label = QLabel("ATS Match Score:", self)
        self.score_bar = QProgressBar(self)
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(0)
        self.score_bar.setFixedHeight(16)
        self.score_bar.setTextVisible(True)
        self.score_bar.setFormat("%v%")
        score_row.addWidget(self.score_label)
        score_row.addWidget(self.score_bar)
        main_layout.addLayout(score_row)

        # -----------------------------------------------------------
        # FORMATTED TEXT AREA (READ-ONLY PREVIEW)
        # -----------------------------------------------------------
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Your tailored resume will appear here...")

        font = QFont("Calibri", 11)
        self.text_edit.setFont(font)

        main_layout.addWidget(self.text_edit)

        # Connect copy behavior
        self.btnCopy.clicked.connect(self._copy_to_clipboard)

    # -----------------------------------------------------------------------------------
    def _copy_to_clipboard(self):
        """Copy the displayed text to the clipboard (plain text)."""
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btnCopy.setText("Copied!")
            QTimer.singleShot(2000, lambda: self.btnCopy.setText("Copy"))

    # -----------------------------------------------------------------------------------
    def _format_resume_text(self, text: str) -> str:
        """Convert plain resume text to HTML with nice formatting."""
        if not text:
            return ""

        lines = text.splitlines()
        html_parts = [
            '<html><body style="font-family: Calibri, sans-serif; font-size: 11pt; line-height: 1.6;">'
        ]

        section_keywords = {
            "experience", "work experience", "professional experience",
            "education", "skills", "summary", "profile", "objective",
            "projects", "certifications", "achievements", "leadership",
            "technical skills", "core competencies",
        }

        for line in lines:
            stripped = line.strip()

            if not stripped:
                html_parts.append("<br>")
                continue

            is_header = False
            if len(stripped) < 60:
                if stripped.isupper() or stripped.istitle():
                    is_header = True
                if stripped.lower() in section_keywords:
                    is_header = True

            if is_header:
                html_parts.append(
                    f'<p style="margin-top: 16px; margin-bottom: 8px;">'
                    f'<b style="color: #54AED5; font-size: 12pt; text-transform: uppercase;">'
                    f'{stripped}</b></p>'
                )
            elif stripped.startswith(("- ", "• ", "* ", "– ", "— ")):
                bullet_text = stripped[2:].strip() if len(stripped) > 2 else stripped
                html_parts.append(
                    f'<p style="margin-left: 20px; margin-top: 4px; margin-bottom: 4px;">'
                    f'• {bullet_text}</p>'
                )
            else:
                html_parts.append(
                    f'<p style="margin-top: 4px; margin-bottom: 4px;">{stripped}</p>'
                )

        html_parts.append("</body></html>")
        return "".join(html_parts)

    # -----------------------------------------------------------
    # Public API
    # -----------------------------------------------------------
    def setText(self, text: str) -> None:
        """Set the text with automatic formatting."""
        formatted_html = self._format_resume_text(text)
        self.text_edit.setHtml(formatted_html)

        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)

    def toPlainText(self) -> str:
        """Get the plain text content."""
        return self.text_edit.toPlainText()

    def setScore(self, score: int) -> None:
        """Update the ATS match score bar with color coding."""
        self.score_bar.setValue(score)
        if score >= 75:
            color = "#22c55e"  # green
        elif score >= 50:
            color = "#f59e0b"  # amber
        else:
            color = "#ef4444"  # red
        self.score_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
        )