"""
Loading Dialog
--------------

Shows an animated loading indicator while AI processes the resume.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMovie
import os


class LoadingDialog(QDialog):
    def __init__(self, message="Tailoring your resume...", parent=None):
        super().__init__(parent)

        # Window setup
        self.setWindowTitle("Processing")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(400, 200)

        # Center on parent
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 400) // 2
            y = parent_geo.y() + (parent_geo.height() - 200) // 2
            self.move(x, y)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Message label
        self.label = QLabel(message, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            """
            QLabel {
                font-size: 14pt;
                font-weight: 600;
                color: #54AED5;
            }
        """
        )
        layout.addWidget(self.label)

        # Progress bar (indeterminate)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)  # Indeterminate mode
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #2A313C;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: #54AED5;
            }
        """
        )
        layout.addWidget(self.progress)

        # Animated dots for "Tailoring..."
        self.dots = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_dots)
        self.timer.start(500)  # Update every 500ms

        self.base_message = message.rstrip(".")

    def _animate_dots(self):
        """Animate the dots after the message."""
        self.dots = "." * ((len(self.dots) + 1) % 4)
        self.label.setText(f"{self.base_message}{self.dots}")

    def setMessage(self, message):
        """Update the loading message."""
        self.base_message = message.rstrip(".")
        self.dots = ""

    def closeEvent(self, event):
        """Stop the timer when dialog closes."""
        self.timer.stop()
        super().closeEvent(event)
