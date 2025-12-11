"""
FilePicker Widget
------------------------------------------------

Reusable widget for selecting a file from disk. Supports signals,
drag-and-drop, placeholder text, and programmatic path setting.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from PyQt6.QtCore import pyqtSignal, Qt


class FilePicker(QWidget):
    fileSelected = pyqtSignal(str)

    def __init__(
        self,
        label_text: str = "File:",
        file_filter: str = "All files (*.*)",
        parent=None,
    ):
        super().__init__(parent)

        self._file_filter = file_filter
        self.setAcceptDrops(True)  # This is to enable drag-and-drop

        # -----------------------------------------------------------
        # UI Elements
        # -----------------------------------------------------------
        self.label = QLabel(label_text, self)

        self.path_display = QLineEdit(self)
        self.path_display.setReadOnly(True)
        self.path_display.setPlaceholderText("Select a file...")
        self.path_display.setProperty("filePicker", True)

        self.button = QPushButton("Browse", self)

        # -----------------------------------------------------------
        # Layout
        # -----------------------------------------------------------
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.path_display)
        layout.addWidget(self.button)

        self.button.clicked.connect(self._on_browse_clicked)

    # ==========================================================
    #   Public Methods
    # ==========================================================
    def path(self) -> str:
        """Return the currently selected file path."""
        return self.path_display.text().strip()

    def setPath(self, path: str) -> None:
        """Programmatically set the file path."""
        self.path_display.setText(path)

    # ==========================================================
    #   File Dialog
    # ==========================================================
    def _on_browse_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            self._file_filter,
        )

        if file_path:
            self.setPath(file_path)
            self.fileSelected.emit(file_path)

    # ==========================================================
    #   Drag-and-Drop Support
    # ==========================================================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.setPath(path)
                self.fileSelected.emit(path)
