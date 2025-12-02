'''
Reusable widget for selecting a file from disk.
'''
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt6.QtCore import pyqtSignal

class FilePicker(QWidget):
    # Simple file picker with label, read-only line edit, and 'Browse' button.

    fileSelected = pyqtSignal(str)
    
    def __init__(self, label_text: str = "File:", file_filter: str = "All files (*.*)", parent=None):
        super().__init__(parent)
        
        self._file_filter = file_filter
        
        self.label = QLabel(label_text, self)
        self.path_display = QLineEdit(self)
        self.path_display.setReadOnly(True)
        
        self.button = QPushButton("Browse", self)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.path_display)
        layout.addWidget(self.button)
        
        self.button.clicked.connect(self._on_browse_clicked)
        
    # --------------------------------------------------------------------------
    
    def _on_browse_clicked(self) -> None:
        # Open a file dialog and emit the selected file path.
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", self._file_filter)
        
        if file_path:
            self.path_display.setText(file_path)
            self.fileSelected.emit(file_path)