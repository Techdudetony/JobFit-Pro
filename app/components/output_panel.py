"""
Panel that displays the tailored resume text and allows easy copying.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QApplication,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer


class OutPutPanel(QWidget):
    # Tailored resume output panel with a header and 'Copy' button.
    def __init__(self, title: str = "Tailored Resume", parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header Row
        header_layout = QHBoxLayout()
        label = QLabel(title, self)
        label.setProperty("panelTitle", True)
        header_layout.addWidget(label)
        header_layout.addStretch()

        self.btnCopy = QPushButton("Copy", self)
        header_layout.addWidget(self.btnCopy)

        main_layout.addLayout(header_layout)
        
        # Score Row
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

        # Text Area
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setPlaceholderText("Your tailored resume will appear here...")
        main_layout.addWidget(self.text_edit)

        self.btnCopy.clicked.connect(self._copy_to_clipboard)

    # --------------------------------------------------------------------------

    def _copy_to_clipboard(self) -> None:
        # Copy the current text to the clipboard.
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.btnCopy.setText("Copied!")
            QTimer.singleShot(2000, lambda: self.btnCopy.setText("Copy"))

    # Convenience helpers used from MainWindow
    def setText(self, text: str) -> None:
        self.text_edit.setPlainText(text)

    def toPlainText(self) -> str:
        return self.text_edit.toPlainText()
    
    def setScore(self, score: int) -> None:
        self.score_bar.setValue(score)
        if score >= 75:
            color = "#22c55e"
        elif score >= 50:
            color = "#f59e0b"
        else:
            color = "#ef4444"
        self.score_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius:4px; }}"
        )
