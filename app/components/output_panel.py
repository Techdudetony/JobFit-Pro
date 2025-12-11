"""
OutputPanel
----------------------------------------------

Displays LLM-generated resume output and provides a simple copy-to-clipboard action.
Can be used anywhere as a reusable widget.
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
        # TEXT AREA (OUTPUT ONLY)
        # -----------------------------------------------------------
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Your tailored resume will appear here...")

        main_layout.addWidget(self.text_edit)

        # Connect copy behavior
        self.btnCopy.clicked.connect(self._copy_to_clipboard)

    # -----------------------------------------------------------------------------------
    def _copy_to_clipboard(self):
        """Copy the displayed text to the clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    # -----------------------------------------------------------
    # Public API
    # -----------------------------------------------------------
    def setText(self, text: str) -> None:
        self.text_edit.setPlainText(text)

    def toPlainText(self) -> str:
        return self.text_edit.toPlainText()
