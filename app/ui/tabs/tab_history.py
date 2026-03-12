# app/ui/tabs/tab_history.py
"""
History Tab — JobFit Pro
------------------------

Displays every tailoring session with:
- Company, Role, Open Resume (PDF), Created timestamp, ATS replay, Delete
- Timestamps formatted as human-readable strings
- "View ATS" button opens the ATS drawer pre-populated from stored analysis
- Editable Company / Role fields
"""

import os
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
    QLabel,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor, QIcon

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "tailoring_history.json")
ASSETS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "assets", "icons"
)

os.makedirs(DATA_DIR, exist_ok=True)

COL_COMPANY = 0
COL_ROLE = 1
COL_FILE = 2
COL_CREATED = 3
COL_ATS = 4
COL_COVER = 5
COL_DELETE = 6


def _fmt_timestamp(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw)
        # strftime with %-I works on Linux/Mac; %#I on Windows
        try:
            return dt.strftime("%-m/%-d/%Y  %-I:%M %p")
        except ValueError:
            return dt.strftime("%m/%d/%Y  %I:%M %p")
    except Exception:
        return raw


class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ats_panel_ref = None
        self._build_ui()
        self.load_history()

    def set_ats_panel(self, panel):
        self._ats_panel_ref = panel

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        lbl = QLabel("Tailoring History")
        lbl.setProperty("panelTitle", True)
        header.addWidget(lbl)
        header.addStretch()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_delete = QPushButton("Delete Selected")
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_delete)
        root.addLayout(header)

        self.table = QTableWidget(0, 7)
        self.table.setObjectName("historyTable")
        self.table.setHorizontalHeaderLabels(
            ["Company", "Role", "Resume", "Created", "ATS", "Cover Letter", ""]
        )
        self.table.setColumnWidth(COL_COMPANY, 170)
        self.table.setColumnWidth(COL_ROLE, 200)
        self.table.setColumnWidth(COL_FILE, 100)
        self.table.setColumnWidth(COL_CREATED, 155)
        self.table.setColumnWidth(COL_ATS, 80)
        self.table.setColumnWidth(COL_COVER, 100)
        self.table.setColumnWidth(COL_DELETE, 44)
        self.table.setSortingEnabled(
            False
        )  # sorting during/after edit was overwriting changes
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.cellClicked.connect(self._handle_cell_click)
        self.table.itemChanged.connect(self._save_edit)
        root.addWidget(self.table)

        self.btn_refresh.clicked.connect(self.load_history)
        self.btn_delete.clicked.connect(self._delete_selected)

    def load_history(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for idx, entry in enumerate(self._read_history()):
            self._add_row(entry, json_index=idx)
        self.table.blockSignals(False)

    def _add_row(self, entry: dict, json_index: int = 0):
        row = self.table.rowCount()
        self.table.insertRow(row)

        company = entry.get("company", "")
        role = entry.get("role", "")
        file_link = (
            entry.get("resume_url") or entry.get("local_pdf") or entry.get("file") or ""
        )
        created = _fmt_timestamp(entry.get("timestamp", ""))
        ats_result = entry.get("ats_result")

        # Company (editable)
        item_co = QTableWidgetItem(company)
        item_co.setFlags(item_co.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, COL_COMPANY, item_co)

        # Role (editable)
        item_ro = QTableWidgetItem(role)
        item_ro.setFlags(item_ro.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, COL_ROLE, item_ro)

        # Resume file link
        item_f = QTableWidgetItem("Open PDF" if file_link else "—")
        item_f.setData(Qt.ItemDataRole.UserRole, file_link)
        if file_link:
            item_f.setForeground(QColor("#54AED5"))
        item_f.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(row, COL_FILE, item_f)

        # Created timestamp (read-only) — also stores json_index in UserRole for safe write-back
        item_cr = QTableWidgetItem(created)
        item_cr.setData(Qt.ItemDataRole.UserRole, json_index)
        item_cr.setFlags(item_cr.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, COL_CREATED, item_cr)

        # ATS button or dash
        if ats_result:
            btn_ats = QPushButton("View ATS")
            btn_ats.setFixedHeight(26)
            btn_ats.setStyleSheet(
                "QPushButton{background:#1E3A5F;color:#54AED5;border:1px solid #54AED5;"
                "border-radius:4px;font-size:8pt;font-weight:600;padding:2px 6px;}"
                "QPushButton:hover{background:#2A4E78;}"
            )
            btn_ats.clicked.connect(lambda _, r=ats_result: self._open_ats(r))
            wrap_ats = QWidget()
            wl = QHBoxLayout(wrap_ats)
            wl.addStretch()
            wl.addWidget(btn_ats)
            wl.addStretch()
            wl.setContentsMargins(2, 2, 2, 2)
            self.table.setCellWidget(row, COL_ATS, wrap_ats)
        else:
            item_no = QTableWidgetItem("—")
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_no.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item_no.setForeground(QColor("#475569"))
            self.table.setItem(row, COL_ATS, item_no)

        # Cover letter button or dash
        cover_letter = entry.get("cover_letter", "")
        if cover_letter:
            btn_cover = QPushButton("View")
            btn_cover.setFixedHeight(26)
            btn_cover.setStyleSheet(
                "QPushButton{background:#1A3A2A;color:#34D399;border:1px solid #34D399;"
                "border-radius:4px;font-size:8pt;font-weight:600;padding:2px 6px;}"
                "QPushButton:hover{background:#22543D;}"
            )
            btn_cover.clicked.connect(
                lambda _, cl=cover_letter: self._open_cover_letter(cl)
            )
            wrap_cv = QWidget()
            wl_cv = QHBoxLayout(wrap_cv)
            wl_cv.addStretch()
            wl_cv.addWidget(btn_cover)
            wl_cv.addStretch()
            wl_cv.setContentsMargins(2, 2, 2, 2)
            self.table.setCellWidget(row, COL_COVER, wrap_cv)
        else:
            item_cv = QTableWidgetItem("—")
            item_cv.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cv.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item_cv.setForeground(QColor("#475569"))
            self.table.setItem(row, COL_COVER, item_cv)

        # Delete button
        trash_path = os.path.join(ASSETS, "trash.svg")
        btn_del = QPushButton()
        if os.path.exists(trash_path):
            btn_del.setIcon(QIcon(trash_path))
        else:
            btn_del.setText("✕")
        btn_del.setFixedSize(28, 28)
        btn_del.clicked.connect(lambda _, ji=json_index: self._delete_row(ji))
        wrap_del = QWidget()
        wl2 = QHBoxLayout(wrap_del)
        wl2.addStretch()
        wl2.addWidget(btn_del)
        wl2.addStretch()
        wl2.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, COL_DELETE, wrap_del)

    def _handle_cell_click(self, row, col):
        if col != COL_FILE:
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
            QMessageBox.warning(
                self, "File Missing", "The resume PDF could not be found."
            )

    def _open_ats(self, result: dict):
        if not self._ats_panel_ref:
            QMessageBox.information(
                self,
                "ATS Panel",
                "Switch to the Tailor tab first, then click View ATS.",
            )
            return
        main = self.window()
        if hasattr(main, "ui") and hasattr(main.ui, "sidebarNav"):
            main.ui.sidebarNav.set_tab(0)
        self._ats_panel_ref.load_from_history(result)

    def _open_cover_letter(self, text: str):
        """Show the saved cover letter in a simple read-only dialog."""
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QTextEdit,
            QPushButton,
            QHBoxLayout,
            QApplication,
        )

        dlg = QDialog(self)
        dlg.setWindowTitle("Saved Cover Letter")
        dlg.setMinimumSize(640, 520)
        layout = QVBoxLayout(dlg)

        editor = QTextEdit(dlg)
        editor.setFont(
            __import__("PyQt6.QtGui", fromlist=["QFont"]).QFont("Calibri", 11)
        )
        editor.setPlainText(text)
        layout.addWidget(editor)

        btn_row = QHBoxLayout()
        btn_copy = QPushButton("Copy", dlg)
        btn_copy.clicked.connect(
            lambda: QApplication.clipboard().setText(editor.toPlainText())
        )
        btn_close = QPushButton("Close", dlg)
        btn_close.clicked.connect(dlg.accept)
        btn_row.addStretch()
        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        dlg.exec()

    def _save_edit(self, item):
        col = item.column()
        if col not in (COL_COMPANY, COL_ROLE):
            return
        # json_index is stored on the Created cell — never touched by editing
        created_item = self.table.item(item.row(), COL_CREATED)
        if not created_item:
            return
        json_index = created_item.data(Qt.ItemDataRole.UserRole)
        if json_index is None:
            return
        history = self._read_history()
        if json_index >= len(history):
            return
        if col == COL_COMPANY:
            history[json_index]["company"] = item.text()
        elif col == COL_ROLE:
            history[json_index]["role"] = item.text()
        history[json_index]["last_updated"] = datetime.now().isoformat()
        # Block signals so writing back doesn't re-trigger itemChanged
        self.table.blockSignals(True)
        self._write_history(history)
        self.table.blockSignals(False)

    def _delete_row(self, json_index: int):
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Delete this history entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        history = self._read_history()
        if json_index < len(history):
            del history[json_index]
            self._write_history(history)
        self.load_history()

    def _delete_selected(self):
        # Collect unique json_indices from the UserRole of the Company cell
        selected_rows = {i.row() for i in self.table.selectedIndexes()}
        if not selected_rows:
            QMessageBox.information(self, "Nothing Selected", "No rows selected.")
            return
        json_indices = set()
        for r in selected_rows:
            cr_item = self.table.item(r, COL_CREATED)
            if cr_item:
                ji = cr_item.data(Qt.ItemDataRole.UserRole)
                if ji is not None:
                    json_indices.add(ji)
        if not json_indices:
            return
        reply = QMessageBox.question(
            self,
            "Delete Selected",
            f"Delete {len(json_indices)} entr{'y' if len(json_indices)==1 else 'ies'}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        history = self._read_history()
        # Delete in reverse order so earlier indices stay valid
        for ji in sorted(json_indices, reverse=True):
            if ji < len(history):
                del history[ji]
        self._write_history(history)
        self.load_history()

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
