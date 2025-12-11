"""
Tailoring History Window — Enhanced Version
-------------------------------------------
Displays and manages a table of all tailored resume history entries.

Features:
- View Company, Role, File Link, Created Timestamp, Last Updated Timestamp
- Editable fields (Company, Role, Created Timestamp)
- Auto-updates 'last_updated' timestamp when edited
- Single delete button per row
- Bulk delete (multi-select deletion)
- Sorting enabled
- Opens Supabase URLs or local files
"""

import os
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor, QIcon


# ------------------------------------------------------------
# HISTORY FILE PATH
# ------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "tailoring_history.json")

ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons")


class TailoringHistoryWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("historyDialog")
        self.setWindowTitle("Tailoring History")
        self.resize(900, 480)

        layout = QVBoxLayout(self)

        # ------------------------------------------------------------
        # TABLE WIDGET
        # ------------------------------------------------------------
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("historyTable")

        self.table.setHorizontalHeaderLabels(
            ["Company", "Role", "File", "Created", "Updated", ""]
        )

        self.table.setColumnWidth(0, 170)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(2, 260)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 50)

        # Sorting + Multi-select
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        layout.addWidget(self.table)

        # Click handler for file links
        self.table.cellClicked.connect(self.handle_cell_click)

        # Handle saving edited fields
        self.table.itemChanged.connect(self.save_edited_field)

        # ------------------------------------------------------------
        # BUTTON BAR
        # ------------------------------------------------------------
        btn_row = QHBoxLayout()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_delete_selected = QPushButton("Delete Selected")
        self.btn_close = QPushButton("Close")

        btn_row.addWidget(self.btn_refresh)
        btn_row.addWidget(self.btn_delete_selected)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_close)

        layout.addLayout(btn_row)

        # Connections
        self.btn_refresh.clicked.connect(self.load_history)
        self.btn_delete_selected.clicked.connect(self.delete_selected_rows)
        self.btn_close.clicked.connect(self.close)

        # Load on startup
        self.load_history()

    # ============================================================
    # Load All Entries
    # ============================================================
    def load_history(self):
        self.table.blockSignals(True)  # Prevent itemChanged spam
        self.table.setRowCount(0)

        if not os.path.exists(HISTORY_FILE):
            self.table.blockSignals(False)
            return

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

        for entry in history:
            self.add_row(entry)

        self.table.blockSignals(False)

    # ============================================================
    # Populate a Table Row
    # ============================================================
    def add_row(self, entry: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)

        company = entry.get("company", "")
        role = entry.get("role", "")
        file_link = entry.get("resume_url") or entry.get("file") or ""
        created = entry.get("timestamp", "")
        updated = entry.get("last_updated", "")

        # -------------------- Company --------------------
        item_company = QTableWidgetItem(company)
        item_company.setFlags(item_company.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item_company)

        # -------------------- Role ------------------------
        item_role = QTableWidgetItem(role)
        item_role.setFlags(item_role.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, item_role)

        # -------------------- File Link -------------------
        item_file = QTableWidgetItem("Open Resume" if file_link else "")
        item_file.setData(Qt.ItemDataRole.UserRole, file_link)
        item_file.setForeground(QColor("#54AED5"))  # Brand primary
        item_file.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 2, item_file)

        # -------------------- Created Timestamp -----------
        item_created = QTableWidgetItem(created)
        item_created.setFlags(item_created.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, item_created)

        # -------------------- Updated Timestamp -----------
        item_updated = QTableWidgetItem(updated)
        item_updated.setFlags(item_updated.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 4, item_updated)

        # -------------------- Delete Button ----------------
        trash_path = os.path.join(ASSETS, "trash.svg")

        btn_delete = QPushButton()
        if os.path.exists(trash_path):
            btn_delete.setIcon(QIcon(trash_path))
        else:
            btn_delete.setText("X")

        btn_delete.setFixedSize(28, 28)
        btn_delete.clicked.connect(lambda _, r=row: self.delete_row(r))

        wrapper = QWidget()
        wlayout = QHBoxLayout(wrapper)
        wlayout.addStretch()
        wlayout.addWidget(btn_delete)
        wlayout.addStretch()
        wlayout.setContentsMargins(0, 0, 0, 0)

        self.table.setCellWidget(row, 5, wrapper)

    # ============================================================
    # Handle File Link Click
    # ============================================================
    def handle_cell_click(self, row, col):
        if col != 2:
            return

        item = self.table.item(row, col)
        if not item:
            return

        link = item.data(Qt.ItemDataRole.UserRole)
        if not link:
            return

        # Supabase or HTTPS URL
        if link.startswith("http://") or link.startswith("https://"):
            QDesktopServices.openUrl(QUrl(link))
            return

        # Local file
        if os.path.exists(link):
            QDesktopServices.openUrl(QUrl.fromLocalFile(link))
        else:
            QMessageBox.warning(
                self, "File Missing", "This file can no longer be found."
            )

    # ============================================================
    # Save Edited Fields
    # ============================================================
    def save_edited_field(self, item):
        row = item.row()
        col = item.column()

        if col not in (0, 1, 3):  # Only editable fields
            return

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            return

        if row >= len(history):
            return

        # Apply edits
        if col == 0:
            history[row]["company"] = item.text()
        elif col == 1:
            history[row]["role"] = item.text()
        elif col == 3:
            history[row]["timestamp"] = item.text()

        # Update last modified timestamp
        history[row]["last_updated"] = datetime.now().isoformat()

        # Save
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

        # Update UI column
        updated_item = QTableWidgetItem(history[row]["last_updated"])
        updated_item.setFlags(updated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 4, updated_item)

    # ============================================================
    # Single Row Delete
    # ============================================================
    def delete_row(self, row):
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Are you sure you want to delete this entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

        if row < len(history):
            del history[row]

            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)

        self.load_history()

    # ============================================================
    # Multi-Select Delete
    # ============================================================
    def delete_selected_rows(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)

        if not rows:
            QMessageBox.information(self, "Nothing Selected", "No rows selected.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Selected",
            f"Delete {len(rows)} entr{'y' if len(rows)==1 else 'ies'}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

        for r in rows:
            if r < len(history):
                del history[r]

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)

        self.load_history()
