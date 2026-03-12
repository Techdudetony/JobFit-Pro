# app/ui/main_window.py
"""
Main Window UI — Tabbed Layout (v3)
------------------------------------

Structure:
  QMainWindow
  └── central_widget  (QHBoxLayout, no margins)
      ├── SidebarNav          ← binder tab strip (fixed left)
      └── QStackedWidget      ← content area (stretches)
          ├── [0] TailorTab
          ├── [1] HistoryTab
          ├── [2] SettingsTab
          └── [3] CoverLetterTab
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QStackedWidget,
)
from PyQt6.QtCore import Qt

from app.ui.sidebar_nav import SidebarNav
from app.ui.tabs.tab_tailor import TailorTab
from app.ui.tabs.tab_history import HistoryTab
from app.ui.tabs.tab_settings import SettingsTab
from app.ui.tabs.tab_cover_letter import CoverLetterTab


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 820)
        MainWindow.setWindowTitle("JobFit Pro")
        MainWindow.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # ── Root container ────────────────────────────────────────
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName("MainCentral")
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root_layout = QHBoxLayout(self.central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar nav ───────────────────────────────────────────
        self.sidebarNav = SidebarNav(self.central_widget)
        root_layout.addWidget(self.sidebarNav)

        # ── Stacked content area ──────────────────────────────────
        self.stack = QStackedWidget(self.central_widget)
        self.stack.setObjectName("contentStack")
        root_layout.addWidget(self.stack, stretch=1)

        # ── Tabs ──────────────────────────────────────────────────
        self.tabTailor      = TailorTab(self.stack)
        self.tabHistory     = HistoryTab(self.stack)
        self.tabSettings    = SettingsTab(
            settings_panel=self.tabTailor.settingsPanel,
            parent=self.stack,
        )
        self.tabCoverLetter = CoverLetterTab(self.stack)

        self.stack.addWidget(self.tabTailor)       # index 0
        self.stack.addWidget(self.tabHistory)      # index 1
        self.stack.addWidget(self.tabSettings)     # index 2
        self.stack.addWidget(self.tabCoverLetter)  # index 3

        # ── Wire sidebar → stack ──────────────────────────────────
        self.sidebarNav.tabChanged.connect(self._on_tab_changed)

        MainWindow.setCentralWidget(self.central_widget)

        # ── Expose all widget names window_main.py expects ────────
        # Tailor tab widgets
        self.inputJobURL    = self.tabTailor.inputJobURL
        self.btnFetchJob    = self.tabTailor.btnFetchJob
        self.btnUseManualJob= self.tabTailor.btnUseManualJob
        self.settingsPanel  = self.tabTailor.settingsPanel
        self.resumePicker   = self.tabTailor.resumePicker
        self.btnLoadResume  = self.tabTailor.btnLoadResume
        self.btnLastResume  = self.tabTailor.btnLastResume
        self.jobPreview     = self.tabTailor.jobPreview
        self.resumePreview  = self.tabTailor.resumePreview
        self.outputPanel    = self.tabTailor.outputPanel
        self.outputPreview  = self.tabTailor.outputPreview
        self.btnTailor      = self.tabTailor.btnTailor
        self.btnExport      = self.tabTailor.btnExport
        self.btnExportPDF   = self.tabTailor.btnExportPDF

    def _on_tab_changed(self, index: int):
        self.stack.setCurrentIndex(index)

        # Refresh history table whenever user switches to it
        if index == 1:
            self.tabHistory.load_history()