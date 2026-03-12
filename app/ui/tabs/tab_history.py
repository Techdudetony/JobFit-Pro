# app/ui/tabs/tab_history.py
"""
History Tab — JobFit Pro
------------------------

Embeds the tailoring history table directly into the tab
(no separate dialog needed — it lives here now).
"""

import os
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLabel,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor, QIcon

DATA_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "tailoring_history.json")
ASSETS       = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "icons"
)

os.makedirs(DATA_DIR, exist_ok=True)


class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_history()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        lbl = QLabel("Tailoring History")
        lbl.setProperty("panelTitle", True)
        header.addWidget(lbl)
        header.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_delete  = QPushButton("Delete Selected")
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_delete)
        root.addLayout(header)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("historyTable")
        self.table.setHorizontalHeaderLabels(
            ["Company", "Role", "File", "Created", ""]
        )
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 260)
        self.table.setColumnWidth(3, 160)
        self.table.setColumnWidth(4, 50)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.cellClicked.connect(self._handle_cell_click)
        self.table.itemChanged.connect(self._save_edit)
        root.addWidget(self.table)

        # Wire buttons
        self.btn_refresh.clicked.connect(self.load_history)
        self.btn_delete.clicked.connect(self._delete_selected)

    # ----------------------------------------------------------
    def load_history(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        history = self._read_history()
        for entry in history:
            self._add_row(entry)

        self.table.blockSignals(False)

    def _add_row(self, entry: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)

        company   = entry.get("company", "")
        role      = entry.get("role", "")
        file_link = entry.get("resume_url") or entry.get("file") or ""
        created   = entry.get("timestamp", "")

        item_co = QTableWidgetItem(company)
        item_co.setFlags(item_co.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, item_co)

        item_ro = QTableWidgetItem(role)
        item_ro.setFlags(item_ro.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, item_ro)

        item_f = QTableWidgetItem("Open Resume" if file_link else "")
        item_f.setData(Qt.ItemDataRole.UserRole, file_link)
        item_f.setForeground(QColor("#54AED5"))
        item_f.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, 2, item_f)

        item_cr = QTableWidgetItem(created)
        item_cr.setFlags(item_cr.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, item_cr)

        # Delete button
        trash_path = os.path.join(ASSETS, "trash.svg")
        btn_del = QPushButton()
        if os.path.exists(trash_path):
            btn_del.setIcon(QIcon(trash_path))
        else:
            btn_del.setText("✕")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda _, r=row: self._delete_row(r))

        wrap = QWidget()
        wl   = QHBoxLayout(wrap)
        wl.addStretch()
        wl.addWidget(btn_del)
        wl.addStretch()
        wl.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 4, wrap)

    # ----------------------------------------------------------
    def _handle_cell_click(self, row, col):
        if col != 2:
            return
        item = self.table.item(row, col)
        if not item:
            return
        link = item.data(Qt.ItemDataRole.UserRole)
        if not link:
            return
        if link.startswith("http://") or link.startswith("https://"):
            QDesktopServices.openUrl(QUrl(link))
        elif os.path.exists(link):
            QDesktopServices.openUrl(QUrl.fromLocalFile(link))
        else:
            QMessageBox.warning(self, "File Missing", "This file can no longer be found.")

    def _save_edit(self, item):
        row = item.row()
        col = item.column()
        if col not in (0, 1, 3):
            return
        history = self._read_history()
        if row >= len(history):
            return
        if col == 0:
            history[row]["company"] = item.text()
        elif col == 1:
            history[row]["role"] = item.text()
        elif col == 3:
            history[row]["timestamp"] = item.text()
        history[row]["last_updated"] = datetime.now().isoformat()
        self._write_history(history)

    def _delete_row(self, row):
        reply = QMessageBox.question(
            self, "Delete Entry", "Delete this entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        history = self._read_history()
        if row < len(history):
            del history[row]
            self._write_history(history)
        self.load_history()

    def _delete_selected(self):
        rows = sorted(
            {i.row() for i in self.table.selectedIndexes()}, reverse=True
        )
        if not rows:
            QMessageBox.information(self, "Nothing Selected", "No rows selected.")
            return
        reply = QMessageBox.question(
            self, "Delete Selected",
            f"Delete {len(rows)} entr{'y' if len(rows)==1 else 'ies'}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        history = self._read_history()
        for r in rows:
            if r < len(history):
                del history[r]
        self._write_history(history)
        self.load_history()

    # ----------------------------------------------------------
    def _read_history(self) -> list:
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _write_history(self, history: list):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)