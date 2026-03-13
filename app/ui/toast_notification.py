# app/ui/toast_notification.py
"""
ToastNotification — JobFit Pro
--------------------------------
Slim slide-in notification anchored to the bottom-right of the parent window.
Auto-dismisses after `duration` ms. Clickable to dismiss early.

Usage:
    toast = ToastNotification("✅ ATS Analysis ready!", parent=self)
    toast.show_toast()
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    pyqtProperty,
    QByteArray,
)
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont


TOAST_W = 320
TOAST_H = 52
MARGIN = 16  # distance from parent bottom-right corner
SLIDE_DIST = 60  # px it slides up from bottom
ANIM_IN_MS = 260
ANIM_OUT_MS = 200


class ToastNotification(QWidget):

    # Preset styles: (icon, bg_color, border_color, text_color)
    STYLES = {
        "success": ("✅", "#0F2A1E", "#34D399", "#34D399"),
        "info": ("ℹ️", "#0C1E30", "#54AED5", "#54AED5"),
        "warning": ("⚠️", "#2A1A00", "#FBBF24", "#FBBF24"),
        "error": ("❌", "#2A0A0A", "#F87171", "#F87171"),
    }

    def __init__(
        self,
        message: str,
        parent=None,
        style: str = "info",
        duration: int = 4000,
    ):
        super().__init__(parent)

        self._message = message
        self._duration = duration
        self._style = self.STYLES.get(style, self.STYLES["info"])
        self._opacity = 0.0

        # Frameless, always-on-top within parent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(TOAST_W, TOAST_H)

        self._build_ui()

        # Animation objects (reused)
        self._pos_anim = QPropertyAnimation(self, QByteArray(b"pos"))
        self._pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ------------------------------------------------------------------
    def _build_ui(self):
        icon_char, _, _, text_color = self._style

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon_char)
        icon_lbl.setFixedWidth(20)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        msg_lbl = QLabel(self._message)
        msg_lbl.setStyleSheet(f"color: {text_color}; font-size: 9pt; font-weight: 500;")
        msg_lbl.setWordWrap(False)
        layout.addWidget(msg_lbl, 1)

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(20, 20)
        btn_x.setStyleSheet(
            "QPushButton { background: transparent; color: #64748B; border: none; "
            "font-size: 10pt; } QPushButton:hover { color: #CBD5E1; }"
        )
        btn_x.clicked.connect(self._dismiss)
        layout.addWidget(btn_x)

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        _, bg, border, _ = self._style
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self._opacity)

        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)
        p.fillPath(path, QColor(bg))

        from PyQt6.QtGui import QPen

        p.setPen(QPen(QColor(border), 1))
        p.drawPath(path)
        p.end()

    # ------------------------------------------------------------------
    def _target_pos(self) -> QPoint:
        """Bottom-right of parent, above the margin line."""
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
        else:
            pw, ph = 1200, 800
        x = pw - TOAST_W - MARGIN
        y = ph - TOAST_H - MARGIN
        return QPoint(x, y)

    def _offscreen_pos(self) -> QPoint:
        """Starting position below the visible area."""
        p = self._target_pos()
        return QPoint(p.x(), p.y() + SLIDE_DIST)

    # ------------------------------------------------------------------
    def show_toast(self):
        """Animate in, wait, animate out."""
        self.move(self._offscreen_pos())
        self.show()
        self.raise_()

        # Fade/slide in
        self._opacity = 0.0
        self._animate_opacity_to(1.0, ANIM_IN_MS)

        self._pos_anim.stop()
        self._pos_anim.setDuration(ANIM_IN_MS)
        self._pos_anim.setStartValue(self._offscreen_pos())
        self._pos_anim.setEndValue(self._target_pos())
        self._pos_anim.start()

        # Auto-dismiss timer
        QTimer.singleShot(self._duration, self._dismiss)

    def _dismiss(self):
        self._animate_opacity_to(0.0, ANIM_OUT_MS)
        QTimer.singleShot(ANIM_OUT_MS + 20, self.hide)

    # ------------------------------------------------------------------
    # Opacity painted manually (WA_TranslucentBackground + no Qt opacity)
    def _animate_opacity_to(self, target: float, duration: int):
        steps = max(duration // 16, 1)
        step_size = (target - self._opacity) / steps
        current = [self._opacity]

        def _tick():
            current[0] += step_size
            self._opacity = max(0.0, min(1.0, current[0]))
            self.update()
            if (step_size > 0 and self._opacity < target) or (
                step_size < 0 and self._opacity > target
            ):
                QTimer.singleShot(16, _tick)

        _tick()

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        self._dismiss()
