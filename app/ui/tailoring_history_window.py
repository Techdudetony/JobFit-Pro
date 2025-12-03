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
    QMessageBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "tailoring_history.json")


class TailoringHistoryWindow(QDialog):
    """
    Displays the user's past tailored resumes:
    - Company
    - Role
    - File path (clickable)
    - Delete (trash icon)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Tailoring History")
        self.resize(750, 420)

        layout = QVBoxLayout(self)

        # ------------------------------------------------------------------
        #  TABLE SETUP
        # ------------------------------------------------------------------
        # Add 4 columns: Company | Role | File | Delete
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Company", "Role", "File", ""])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 300)
        self.table.setColumnWidth(3, 50)

        layout.addWidget(self.table)

        # ------------------------------------------------------------------
        #  Bottom buttons
        # ------------------------------------------------------------------
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

    # ==================================================================
    #  Load tailoring history from JSON
    # ==================================================================
    def load_history(self):
        """Loads tailoring history into the table."""

        self.table.setRowCount(0)

        if not os.path.exists(HISTORY_FILE):
            return

        # Load JSON
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []

        # Populate table
        for entry in history:
            self._add_row(entry)

    # ==================================================================
    #  Add a single row to the table
    # ==================================================================
    def _add_row(self, entry: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)

        company = entry.get("company", "Unknown")
        role = entry.get("role", "Unknown")
        file_path = entry.get("file", "")

        # ---- Company ----
        self.table.setItem(row, 0, QTableWidgetItem(company))

        # ---- Role ----
        self.table.setItem(row, 1, QTableWidgetItem(role))

        # ---- Clickable File Link ----
        item = QTableWidgetItem(file_path)
        item.setForeground(Qt.blue)
        item.setToolTip("Click to open this resume file")
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # uneditable
        self.table.setItem(row, 2, item)

        # Connect click event
        self.table.cellClicked.connect(self._handle_cell_click)

        # ---- Trash Button ----
        btn_delete = QPushButton()
        btn_delete.setIcon(QIcon.fromTheme("edit-delete"))
        btn_delete.setToolTip("Delete this entry")
        btn_delete.clicked.connect(lambda _, r=row: self.delete_row(r))

        delete_widget = QWidget()
        delete_layout = QHBoxLayout(delete_widget)
        delete_layout.addStretch()
        delete_layout.addWidget(btn_delete)
        delete_layout.addStretch()
        delete_layout.setContentsMargins(0, 0, 0, 0)

        self.table.setCellWidget(row, 3, delete_widget)

    # ==================================================================
    #  Handle clicking on the File cell → open document
    # ==================================================================
    def _handle_cell_click(self, row, col):
        if col != 2:
            return

        file_path = self.table.item(row, 2).text()

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Missing", "This file no longer exists.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    # ==================================================================
    #  Delete entry from JSON + table
    # ==================================================================
    def delete_row(self, row):
        """Deletes an entry from the JSON history file."""
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Are you sure you want to delete this entry?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Load JSON
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []

        if row >= len(history):
            return

        # Remove entry
        del history[row]

        # Save updated file
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

        # Refresh table
        self.load_history()
