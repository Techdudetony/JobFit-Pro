"""
Help Dialog for JobFit Pro
------------------------------------------------

Provides user documentation, tailoring explanations, and about
information in a polished tabbed dialog.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QTextBrowser,
)
from PyQt6.QtCore import Qt


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpDialog")

        self.setWindowTitle("Help & Documentation")
        self.setMinimumSize(620, 520)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # -----------------------------------------------------------
        # HEADER
        # -----------------------------------------------------------
        title = QLabel("Help & Documentation", self)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setProperty("panelTitle", True)

        layout.addWidget(title)

        # -----------------------------------------------------------
        # TAB CONTAINER
        # -----------------------------------------------------------
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_user_guide_tab(), "User Guide")
        self.tabs.addTab(self._build_tailoring_tab(), "How Tailoring Works")
        self.tabs.addTab(self._build_about_tab(), "About JobFit Pro")

        layout.addWidget(self.tabs)

        # -----------------------------------------------------------
        # FOOTER / CLOSE BUTTON
        # -----------------------------------------------------------
        footer = QHBoxLayout()
        footer.addStretch()

        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.close)

        footer.addWidget(btn_close)
        layout.addLayout(footer)

    # ==========================================================
    #  TAB SECTIONS
    # ==========================================================
    def _build_user_guide_tab(self):
        """Main user guide content."""
        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)

        browser.setHtml(
            """
            <h2 style='color:#54AED5;'>Getting Started</h2>
            <p>JobFit Pro helps you tailor your resume to a specific job description using AI.</p>
            
            <h3>Workflow</h3>
            <ol>
                <li><b>Load your resume</b> (PDF or DOCX).</li>    
                <li><b>Paste or fetch</b> a job description via URL.</li>    
                <li>Click <b>Tailor Resume</b> to generate an optimized version.</li>
                <li>Use <b>Export</b> to save as DOCX or PDF.</li>
                <li>View your previous tailoring attempts using the <b>Tools --> Tailoring History</b> menu.</li>
            </ol>
            
            <h3>Tips</h3>
            <ul>
                <li>Use clear job descriptions for best results.</li>
                <li>Enable ATS-friendly formatting for maximum compatibility.</li>
                <li>Experiment with one-page or two-page limits when needed.</li>
            </ul>
        """
        )
        return browser

    def _build_tailoring_tab(self):
        """Explain your AI tailoring logic in friendly language."""
        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)

        browser.setHtml(
            """
            <h2 style='color:#54AED5;'>How Tailoring Works</h2>

            <p>JobFit Pro uses an AI-powered engine to rewrite your resume based on the 
            requirements and language of the selected job description.</p>

            <h3>What the Tailoring Engine Does</h3>
            <ul>
                <li>Extracts key skills and responsibilities from the job description.</li>
                <li>Rewrites your bullet points to emphasize relevant achievements.</li>
                <li>Strengthens measurable impact throughout your resume.</li>
                <li>Preserves your resume structure while making improvements.</li>
                <li>Optimizes formatting for ATS systems (when enabled).</li>
            </ul>

            <h3>Length Controls</h3>
            <ul>
                <li><b>1–2 pages:</b> Balanced tailoring with full content.</li>
                <li><b>Strict 1 page:</b> Reduces older/less relevant items.</li>
            </ul>
        """
        )
        return browser

    def _build_about_tab(self):
        """Version info, credits, etc."""
        browser = QTextBrowser(self)
        browser.setHtml(
            """
            <h2 style='color:#54AED5;'>About JobFit Pro</h2>

            <p><b>JobFit Pro</b> is a resume optimization tool designed to help job seekers 
            present the strongest possible version of their experience.</p>

            <h3>Features</h3>
            <ul>
                <li>AI-powered resume tailoring</li>
                <li>Smart job description parsing</li>
                <li>ATS-friendly output</li>
                <li>PDF and DOCX export</li>
                <li>Cloud storage via Supabase</li>
            </ul>

            <p style='margin-top:12px; color:#D7DDA8;'>
                Built with ♥ using Python, PyQt6, and modern AI technologies.
            </p>
        """
        )
        return browser
