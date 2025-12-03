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
from PyQt6.QtGui import QDesktopServices, QIcon, QColor

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
      - File (local path or Supabase URL)
      - Delete (trash icon)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Tailoring History")
        self.resize(750, 420)

        layout = QVBoxLayout(self)

        # --------------------------------------------------------------
        #  TABLE: Company | Role | File | [Delete]
        # --------------------------------------------------------------
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Company", "Role", "File", ""])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 300)
        self.table.setColumnWidth(3, 50)

        layout.addWidget(self.table)

        # Click handler for "File" column
        self.table.cellClicked.connect(self._handle_cell_click)

        # --------------------------------------------------------------
        #  Bottom buttons
        # --------------------------------------------------------------
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
        """Loads tailoring history into the table from HISTORY_FILE."""
        self.table.setRowCount(0)

        if not os.path.exists(HISTORY_FILE):
            return

        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

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

        # Prefer Supabase URL → fallback to local "file" key
        file_value = entry.get("resume_url") or entry.get("file") or ""

        # ---- Company ----
        self.table.setItem(row, 0, QTableWidgetItem(company))

        # ---- Role ----
        self.table.setItem(row, 1, QTableWidgetItem(role))

        # ---- Clickable File Link ----
        display_text = "Open Resume" if file_value else ""
        link_item = QTableWidgetItem(display_text)
        link_item.setData(Qt.ItemDataRole.UserRole, file_value)
        link_item.setForeground(QColor("#38bdf8"))  # nice link-ish color
        link_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # not editable/select-only
        self.table.setItem(row, 2, link_item)

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
    #  Handle clicking on the File cell → open URL or file
    # ==================================================================
    def _handle_cell_click(self, row: int, col: int):
        """Opens the resume when the File column is clicked."""
        if col != 2:
            return

        item = self.table.item(row, col)
        if not item:
            return

        value = item.data(Qt.ItemDataRole.UserRole)
        if not value:
            return

        # If it looks like a URL → open in browser
        if value.startswith("http://") or value.startswith("https://"):
            QDesktopServices.openUrl(QUrl(value))
            return

        # Otherwise treat as local file path
        if not os.path.exists(value):
            QMessageBox.warning(self, "File Missing", "This file no longer exists.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(value))

    # ==================================================================
    #  Delete entry from JSON + table
    # ==================================================================
    def delete_row(self, row: int):
        """Deletes an entry from the JSON history file and refreshes the table."""
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Are you sure you want to delete this entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

        if row >= len(history):
            return

        # Remove entry, save, and reload UI
        del history[row]

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

        self.load_history()
