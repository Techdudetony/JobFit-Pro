"""
OutputPanel
----------------------------------------------

Displays a beautifully formatted preview of the tailored resume with:
- Styled headers and sections
- Proper spacing and typography
- Read-only formatted view
- Copy-to-clipboard functionality
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor, QColor


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
        # FORMATTED TEXT AREA (READ-ONLY PREVIEW)
        # -----------------------------------------------------------
        self.text_edit = QTextEdit(self)  # Changed from QPlainTextEdit for rich text
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Your tailored resume will appear here...")

        # Set a clean, professional font
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

    # -----------------------------------------------------------------------------------
    def _format_resume_text(self, text: str) -> str:
        """
        Convert plain resume text to HTML with nice formatting.
        Detects headers, bullet points, and applies styling.
        """
        if not text:
            return ""

        lines = text.splitlines()
        html_parts = [
            '<html><body style="font-family: Calibri, sans-serif; font-size: 11pt; line-height: 1.6;">'
        ]

        # Common section headers to detect
        section_keywords = {
            "experience",
            "work experience",
            "professional experience",
            "education",
            "skills",
            "summary",
            "profile",
            "objective",
            "projects",
            "certifications",
            "achievements",
            "leadership",
            "technical skills",
            "core competencies",
        }

        for line in lines:
            stripped = line.strip()

            if not stripped:
                html_parts.append("<br>")
                continue

            # Check if it's a section header
            is_header = False
            if len(stripped) < 60:  # Headers are usually short
                # Check if it's in all caps or title case
                if stripped.isupper() or stripped.istitle():
                    is_header = True
                # Check if it matches known section names
                if stripped.lower() in section_keywords:
                    is_header = True

            if is_header:
                html_parts.append(
                    f'<p style="margin-top: 16px; margin-bottom: 8px;"><b style="color: #54AED5; font-size: 12pt; text-transform: uppercase;">{stripped}</b></p>'
                )
            elif stripped.startswith(("- ", "• ", "* ", "– ", "— ")):
                # Bullet point
                bullet_text = stripped[2:].strip() if len(stripped) > 2 else stripped
                html_parts.append(
                    f'<p style="margin-left: 20px; margin-top: 4px; margin-bottom: 4px;">• {bullet_text}</p>'
                )
            else:
                # Regular text
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

        # Scroll to top
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)

    def toPlainText(self) -> str:
        """Get the plain text content."""
        return self.text_edit.toPlainText()
