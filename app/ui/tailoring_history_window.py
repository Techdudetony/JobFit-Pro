import os
import json
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QWidget,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt

# Persistent data file
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "tailoring_history.json")


class TailoringHistoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Tailoring History")
        self.resize(700, 400)

        layout = QVBoxLayout(self)

        # ------------------------------------------------------------
        # TABLE
        # ------------------------------------------------------------
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Company", "Role", "File"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # ------------------------------------------------------------
        # BOTTOM BUTTONS
        # ------------------------------------------------------------
        btn_row = QHBoxLayout()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_close = QPushButton("Close")

        btn_row.addWidget(self.btn_refresh)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_close)

        layout.addLayout(btn_row)

        # Events
        self.btn_close.clicked.connect(self.close)
        self.btn_refresh.clicked.connect(self.load_history)

        # Initial load
        self.load_history()

    # ------------------------------------------------------------
    def load_history(self):
        """Loads history JSON file into table."""
        self.table.setRowCount(0)

        if not os.path.exists(HISTORY_FILE):
            return

        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []

        for entry in history:
            row = self.table.rowCount()
            self.table.insertRow(row)

            company = entry.get("company", "Unknown")
            role = entry.get("role", "Unknown")
            file = entry.get("file", "")

            self.table.setItem(row, 0, QTableWidgetItem(company))
            self.table.setItem(row, 1, QTableWidgetItem(role))
            self.table.setItem(row, 2, QTableWidgetItem(file))
