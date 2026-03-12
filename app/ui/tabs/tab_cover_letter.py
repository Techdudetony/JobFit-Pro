# app/ui/tabs/tab_cover_letter.py
"""
Cover Letter Tab — JobFit Pro
------------------------------

Placeholder for the upcoming AI cover letter generator.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt


class CoverLetterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel("✉️")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 48pt;")

        title = QLabel("Cover Letter Generator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 20pt; font-weight: 700; color: #54AED5; margin-top: 12px;"
        )

        subtitle = QLabel(
            "AI-powered cover letters tailored to your resume\n"
            "and the specific job description — coming soon."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 11pt; color: #64748B; margin-top: 8px; line-height: 1.6;"
        )
        subtitle.setWordWrap(True)

        badge = QLabel("Coming Soon")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background-color: #1E293B;
                color: #54AED5;
                border: 1px solid #54AED5;
                border-radius: 12px;
                padding: 6px 20px;
                font-size: 10pt;
                font-weight: 600;
                margin-top: 16px;
            }
        """)
        badge.setFixedWidth(140)

        root.addStretch()
        root.addWidget(icon_lbl)
        root.addWidget(title)
        root.addWidget(subtitle)

        badge_row = QVBoxLayout()
        badge_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_row.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addLayout(badge_row)
        root.addStretch()