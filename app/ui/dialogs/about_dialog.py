"""
About Dialog for JobFit Pro
---------------------------

A clean, branded dialog that displays application information,
version details, and developer credits.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
)
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AboutDialog")

        self.setWindowTitle("About JobFit Pro")
        self.setFixedSize(480, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ---------------------------------------------------------
        # Header + Logo Section
        # ---------------------------------------------------------
        header_widget = QWidget(self)
        header_layout = QHBoxLayout(header_widget)

        # Placeholder for future logo support
        # QLabel with property can be styled OR replaced with an SVG

        title_label = QLabel("JobFit Pro", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet(
            """
            font-size: 26px;
            font-weight: 700;
            color: #54AED5;
        """
        )

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addWidget(header_widget)

        # ---------------------------------------------------------
        # Version Info
        # ---------------------------------------------------------
        version_label = QLabel("Version 1.0.0", self)
        version_label.setStyleSheet(
            """
            font-size: 13px;
            color: #D7DDA8;
        """
        )
        layout.addWidget(version_label)

        # ---------------------------------------------------------
        # About Text
        # ---------------------------------------------------------
        about_label = QLabel(self)
        about_label.setWordWrap(True)
        about_label.setText(
            """
            <p>
            <b>JobFit Pro</b> is a modern desktop application designed to help job seekers tailor their resumes 
            to specific job descriptions using advanced AI-powered language models.
            </p>

            <p>
            It analyzes your resume, evaluates job listings, and generates 
            optimized, ATS-friendly versions that highlight relevant skills, 
            achievements, and experience.
            </p>

            <p>
            Built using Python, PyQt6, and OpenAI technologies.
            </p>
        """
        )
        layout.addWidget(about_label)

        # ---------------------------------------------------------
        # Tech Stack
        # ---------------------------------------------------------
        tech_label = QLabel(self)
        tech_label.setWordWrap(True)
        tech_label.setText(
            """
            <h3 style='color:#54AED5;'>Technology Stack</h3>
            <ul>
                <li>Python 3.11+</li>
                <li>PyQt6 UI Framework</li>
                <li>OpenAI LLM Engine</li>
                <li>Supabase Auth + Storage</li>
                <li>PDF & DOCX Processing Backends</li>
            </ul>
        """
        )
        layout.addWidget(tech_label)

        # ---------------------------------------------------------
        # Developer Credit
        # ---------------------------------------------------------
        credit_label = QLabel(
            "<p style='color:#EFA8B8; font-size:12px;'>Developed by Antonio Lee</p>",
            self,
        )
        layout.addWidget(credit_label)

        layout.addStretch()

        # ---------------------------------------------------------
        # Footer – Close Button
        # ---------------------------------------------------------
        footer = QHBoxLayout()
        footer.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.close)

        footer.addWidget(close_btn)
        layout.addLayout(footer)
