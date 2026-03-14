# app/ui/sidebar_nav.py
"""
SidebarNav — JobFit Pro
-----------------------

Vertical binder-style tab strip.

Each tab:
- Shows an icon + label stacked vertically
- Active tab slides left (extends width) + bold label
- Animated via QPropertyAnimation on a per-tab width property
- Left accent bar in brand color on active tab
"""

import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    pyqtSignal, pyqtProperty, QByteArray,
)
from PyQt6.QtGui import QPainter, QColor, QPixmap, QFont, QPen, QBrush

# ---------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------
TAB_WIDTH_INACTIVE = 72    # resting width (px)
TAB_WIDTH_ACTIVE   = 96    # extended width when active
TAB_HEIGHT         = 90    # fixed height per tab
ACCENT_BAR_W       = 4     # left accent bar thickness
ICON_SIZE          = 28    # icon render size
ANIM_DURATION      = 180   # ms

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets", "icons",
)


# ==================================================================
# Single Tab Button
# ==================================================================
class _TabButton(QWidget):
    clicked = pyqtSignal(int)   # emits its own index

    def __init__(self, index: int, icon_name: str, label: str, parent=None):
        super().__init__(parent)
        self._index      = index
        self._label      = label
        self._active     = False
        self._tab_width  = float(TAB_WIDTH_INACTIVE)
        self._badge      = False   # shows notification dot when True

        # Load icon — generate a light-tinted version for dark mode
        icon_path = os.path.join(ICONS_DIR, icon_name)
        if os.path.exists(icon_path):
            raw = QPixmap(icon_path)
            self._pixmap       = raw
            self._pixmap_light = self._tint_pixmap(raw, QColor(200, 210, 220))
        else:
            self._pixmap       = QPixmap()
            self._pixmap_light = QPixmap()

        self.setFixedHeight(TAB_HEIGHT)
        self.setFixedWidth(TAB_WIDTH_INACTIVE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Animation on _tab_width
        self._anim = QPropertyAnimation(self, QByteArray(b"tab_width"))
        self._anim.setDuration(ANIM_DURATION)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ---- animatable property ----
    def get_tab_width(self) -> float:
        return self._tab_width

    def set_tab_width(self, val: float):
        self._tab_width = val
        self.setFixedWidth(int(val))
        self.update()

    tab_width = pyqtProperty(float, get_tab_width, set_tab_width)

    # ---- tint helper ----
    @staticmethod
    def _tint_pixmap(source: QPixmap, color: QColor) -> QPixmap:
        """
        Returns a copy of source where all opaque pixels are replaced
        with `color`, preserving the alpha channel.
        Used to make dark PNGs visible on dark backgrounds.
        """
        result = QPixmap(source.size())
        result.fill(Qt.GlobalColor.transparent)
        p = QPainter(result)
        p.drawPixmap(0, 0, source)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(result.rect(), color)
        p.end()
        return result

    # ---- activation ----
    def set_active(self, active: bool):
        self._active = active
        target = float(TAB_WIDTH_ACTIVE if active else TAB_WIDTH_INACTIVE)
        self._anim.stop()
        self._anim.setStartValue(float(self._tab_width))
        self._anim.setEndValue(target)
        self._anim.start()

    def set_badge(self, visible: bool):
        """Show or hide the notification dot."""
        self._badge = visible
        self.update()

    # ---- paint ----
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        # Background
        bg = QColor("#11171F") if self._active else QColor("#0C1117")
        painter.fillRect(0, 0, w, h, bg)

        # Left accent bar (active only)
        if self._active:
            painter.fillRect(0, 8, ACCENT_BAR_W, h - 16, QColor("#54AED5"))

        # Icon — use light tint in dark mode
        is_dark = True
        try:
            import services.theme_manager as tm
            if tm.theme_manager:
                is_dark = tm.theme_manager.is_dark_mode()
        except Exception:
            pass

        pixmap = self._pixmap_light if is_dark else self._pixmap
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                ICON_SIZE, ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            ix = (w - ICON_SIZE) // 2 + (ACCENT_BAR_W // 2)
            iy = 16
            painter.setOpacity(1.0 if self._active else 0.55)
            painter.drawPixmap(ix, iy, scaled)
            painter.setOpacity(1.0)

        # Label
        font = QFont("Segoe UI", 8)
        font.setBold(self._active)
        painter.setFont(font)

        color = QColor("#54AED5") if self._active else QColor("#64748B")
        painter.setPen(QPen(color))

        label_rect = self.rect().adjusted(ACCENT_BAR_W + 2, ICON_SIZE + 20, -2, -6)
        painter.drawText(
            label_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self._label,
        )

        # Subtle right separator line
        painter.setPen(QPen(QColor("#1E293B")))
        painter.drawLine(w - 1, 8, w - 1, h - 8)

        # Notification badge dot (top-right area of icon)
        if self._badge:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#F87171")))
            dot_x = w - 14
            dot_y = 12
            painter.drawEllipse(dot_x, dot_y, 9, 9)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._index)


# ==================================================================
# SidebarNav Container
# ==================================================================
class SidebarNav(QWidget):
    tabChanged = pyqtSignal(int)

    # (icon filename, display label)
    TABS = [
        ("edit.png",     "Tailor"),
        ("history.png",  "History"),
        ("settings.png", "Settings"),
        ("cover.png",    "Cover Letter"),
        ("builder.png",  "Builder"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(TAB_WIDTH_ACTIVE)   # wide enough for active tab
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setObjectName("sidebarNav")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 24, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._buttons: list[_TabButton] = []
        self._current = 0

        for i, (icon, label) in enumerate(self.TABS):
            btn = _TabButton(i, icon, label, self)
            btn.clicked.connect(self._on_tab_clicked)
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

        # Activate first tab
        self._buttons[0].set_active(True)

    def _on_tab_clicked(self, index: int):
        if index == self._current:
            # Still clear badge if user clicks active tab
            self._buttons[index].set_badge(False)
            return
        self._buttons[self._current].set_active(False)
        self._buttons[index].set_active(True)
        # Clear badge when user navigates to that tab
        self._buttons[index].set_badge(False)
        self._current = index
        self.tabChanged.emit(index)

    def set_tab(self, index: int):
        """Programmatically switch tab."""
        self._on_tab_clicked(index)

    def set_badge(self, index: int, visible: bool):
        """Show or hide the notification dot on a tab."""
        if 0 <= index < len(self._buttons):
            self._buttons[index].set_badge(visible)

    def paintEvent(self, event):
        """Draw sidebar background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0C1117"))
        painter.end()