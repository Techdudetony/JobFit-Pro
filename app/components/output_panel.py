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
)
from PyQt6.QtCore import Qt


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

    # Convenience helpers used from MainWindow
    def setText(self, text: str) -> None:
        self.text_edit.setPlainText(text)

    def toPlainText(self) -> str:
        return self.text_edit.toPlainText()
