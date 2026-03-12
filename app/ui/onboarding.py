# app/ui/onboarding.py
"""
Onboarding Tutorial — JobFit Pro
---------------------------------

Interactive tooltip overlay tutorial that highlights actual UI elements.

Features:
- Darkens everything except the current target widget
- Tooltip card auto-positions (above/below/left/right) based on screen space
- 5-step walkthrough in user-defined order
- Shows only on first login; re-triggerable from Help menu
- Completion state saved to config.json
"""

import json
import os
import math
import random

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont, QBrush

# ------------------------------------------------------------------
# Config path for persisting completion state
# ------------------------------------------------------------------
CONFIG_FILE = os.path.join(
    os.path.expanduser("~"), ".jobfitpro", "config.json"
)

CARD_WIDTH  = 320
CARD_HEIGHT = 160  # approximate — adjusts to content
PADDING     = 16   # gap between highlight box and card
SPOT_MARGIN = 8    # extra glow margin around target widget


# ==================================================================
# Step definitions
# ==================================================================
STEPS = [
    {
        "target": "inputJobURL",          # objectName of the widget to highlight
        "title":  "Step 1 — Job Description",
        "body":   (
            "Paste a job posting URL and click 'Fetch Description' to pull the "
            "full job details automatically, or type/paste the description directly "
            "into the text box below and click 'Use Pasted Text'."
        ),
    },
    {
        "target": "resumePicker",
        "title":  "Step 2 — Load Your Resume",
        "body":   (
            "Click 'Browse' to load your resume (PDF or DOCX). Once you've loaded "
            "a resume once, the '↩ Last Resume' button will appear so you can reload "
            "it instantly on future sessions."
        ),
    },
    {
        "target": "settingsPanel",
        "title":  "Step 3 — Tailoring Options",
        "body":   (
            "Choose how the AI should tailor your resume. Enable 'Emphasize job "
            "keywords' for maximum ATS impact, or 'Limit to 1 page' if the role "
            "requires a concise resume. ATS-friendly formatting is on by default."
        ),
    },
    {
        "target": "btnTailor",
        "title":  "Step 4 — Tailor & Score",
        "body":   (
            "Click 'Tailor Resume' to send your resume and job description to the AI. "
            "The tailored result will appear below with an ATS Match Score showing "
            "how well your keywords align with the job."
        ),
    },
    {
        "target": "btnExportDOCX",
        "title":  "Step 5 — Export",
        "body":   (
            "Export your tailored resume as a Word document (DOCX) or PDF. "
            "Your tailoring session is also saved to the History — accessible "
            "any time via Tools → Tailoring History."
        ),
    },
]


# ==================================================================
# Completion State Helpers
# ==================================================================
def _load_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_config(data: dict):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ONBOARDING] Failed to save config: {e}")


def has_completed_onboarding() -> bool:
    return _load_config().get("onboarding_complete", False)


def mark_onboarding_complete():
    cfg = _load_config()
    cfg["onboarding_complete"] = True
    _save_config(cfg)


def reset_onboarding():
    """Call this to force the tutorial to show again."""
    cfg = _load_config()
    cfg["onboarding_complete"] = False
    _save_config(cfg)


# ==================================================================
# Overlay Widget — darkens the whole window
# ==================================================================
class OnboardingOverlay(QWidget):
    """
    Full-window transparent overlay.
    Paints a dark tint over everything except a spotlight rect
    around the current target widget.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setGeometry(parent.rect())
        self._spotlight: QRect = QRect()

    def set_spotlight(self, rect: QRect):
        self._spotlight = rect.adjusted(
            -SPOT_MARGIN, -SPOT_MARGIN, SPOT_MARGIN, SPOT_MARGIN
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Full dark overlay
        path = QPainterPath()
        path.addRect(0, 0, self.width(), self.height())

        # Cut out the spotlight
        if not self._spotlight.isNull():
            spot = QPainterPath()
            spot.addRoundedRect(
                float(self._spotlight.x()),
                float(self._spotlight.y()),
                float(self._spotlight.width()),
                float(self._spotlight.height()),
                8.0, 8.0,
            )
            path = path.subtracted(spot)

        painter.fillPath(path, QColor(0, 0, 0, 180))

        # Glow ring around spotlight
        if not self._spotlight.isNull():
            painter.setPen(QColor("#54AED5"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self._spotlight, 8, 8)

        painter.end()


# ==================================================================
# Tooltip Card Widget
# ==================================================================
class OnboardingCard(QWidget):
    """
    Styled step card with title, body, progress, and nav buttons.
    """

    def __init__(self, parent: QWidget, total_steps: int):
        super().__init__(parent)
        self.setFixedWidth(CARD_WIDTH)
        self.total_steps = total_steps
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("onboardingCard")
        self.setStyleSheet("""
            QWidget#onboardingCard {
                background-color: rgba(12, 17, 23, 200);
                border: 1px solid #54AED5;
                border-radius: 12px;
            }
            QLabel {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # Progress label
        self.lbl_progress = QLabel("1 / 5")
        self.lbl_progress.setStyleSheet("color: #54AED5; font-size: 10pt; font-weight: 600;")
        layout.addWidget(self.lbl_progress)

        # Title
        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 12pt; font-weight: 700;")
        self.lbl_title.setWordWrap(True)
        layout.addWidget(self.lbl_title)

        # Body
        self.lbl_body = QLabel()
        self.lbl_body.setStyleSheet("color: #CBD5E1; font-size: 10pt; line-height: 1.5;")
        self.lbl_body.setWordWrap(True)
        layout.addWidget(self.lbl_body)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_skip = QPushButton("Skip Tutorial")
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: none;
                font-size: 9pt;
            }
            QPushButton:hover { color: #94A3B8; }
        """)
        self.btn_skip.setFixedHeight(28)

        self.btn_back = QPushButton("← Back")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid #2A313C;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 10pt;
            }
            QPushButton:hover { border-color: #54AED5; }
        """)
        self.btn_back.setFixedHeight(32)

        self.btn_next = QPushButton("Next →")
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #54AED5;
                color: #0C1117;
                border-radius: 6px;
                padding: 4px 16px;
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #3D93BB; }
        """)
        self.btn_next.setFixedHeight(32)

        btn_row.addWidget(self.btn_skip)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_back)
        btn_row.addWidget(self.btn_next)
        layout.addLayout(btn_row)

    def update_step(self, step_index: int, step: dict):
        self.lbl_progress.setText(f"{step_index + 1} / {self.total_steps}")
        self.lbl_title.setText(step["title"])
        self.lbl_body.setText(step["body"])
        self.btn_back.setVisible(step_index > 0)
        self.btn_next.setText("Finish ✓" if step_index == self.total_steps - 1 else "Next →")
        self.adjustSize()


# ==================================================================
# Confetti Overlay
# ==================================================================
CONFETTI_COLORS = [
    "#54AED5", "#EFA8B8", "#D7DDA8", "#FFFFFF",
    "#3D93BB", "#F472B6", "#34D399", "#FBBF24",
]

class ConfettiParticle:
    def __init__(self, win_w: int, win_h: int):
        self.x     = random.uniform(0, win_w)
        self.y     = random.uniform(-win_h * 0.3, 0)
        self.vx    = random.uniform(-2, 2)
        self.vy    = random.uniform(4, 9)
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-6, 6)
        self.w     = random.uniform(7, 14)
        self.h     = random.uniform(4, 8)
        self.color = QColor(random.choice(CONFETTI_COLORS))
        self.alpha = 255

    def step(self):
        self.x     += self.vx
        self.y     += self.vy
        self.vy    *= 0.99          # very slight drag
        self.angle += self.spin
        self.alpha  = max(0, self.alpha - 3)   # fade out


class ConfettiOverlay(QWidget):
    """Full-window confetti burst that self-destructs when done."""

    def __init__(self, parent: QWidget, count: int = 140):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setGeometry(parent.rect())
        self.raise_()

        self.particles = [
            ConfettiParticle(self.width(), self.height())
            for _ in range(count)
        ]

        self._timer = QTimer(self)
        self._timer.setInterval(16)          # ~60 fps
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self.show()

    def _tick(self):
        for p in self.particles:
            p.step()

        # Remove fully faded or off-screen particles
        self.particles = [
            p for p in self.particles
            if p.alpha > 0 and p.y < self.height() + 20
        ]

        if not self.particles:
            self._timer.stop()
            self.hide()
            self.deleteLater()
            return

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for p in self.particles:
            color = QColor(p.color)
            color.setAlpha(p.alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)

            painter.save()
            painter.translate(p.x, p.y)
            painter.rotate(p.angle)
            painter.drawRoundedRect(
                QRectF(-p.w / 2, -p.h / 2, p.w, p.h), 2, 2
            )
            painter.restore()

        painter.end()


# ==================================================================
# Onboarding Manager — orchestrates everything
# ==================================================================
class OnboardingManager:
    """
    Usage:
        manager = OnboardingManager(main_window)
        manager.start()          # shows tutorial
        manager.start(force=True) # re-show even if completed
    """

    def __init__(self, main_window):
        self.window   = main_window
        self.overlay  = None
        self.card     = None
        self.step_idx = 0

    def start(self, force: bool = False):
        if not force and has_completed_onboarding():
            return

        self.step_idx = 0
        self._build_overlay()
        self._show_step(0)

    def _build_overlay(self):
        # Tear down any existing overlay
        self._cleanup()

        self.overlay = OnboardingOverlay(self.window)
        self.overlay.resize(self.window.size())
        self.overlay.show()
        self.overlay.raise_()

        self.card = OnboardingCard(self.window, len(STEPS))
        self.card.btn_next.clicked.connect(self._next)
        self.card.btn_back.clicked.connect(self._back)
        self.card.btn_skip.clicked.connect(self._skip)
        self.card.show()
        self.card.raise_()

    def _find_widget(self, object_name: str):
        """Recursively search for a widget by objectName."""
        return self.window.findChild(QWidget, object_name)

    def _show_step(self, index: int):
        self.step_idx = index
        step = STEPS[index]

        target = self._find_widget(step["target"])

        if target and target.isVisible():
            # Map target rect to main window coordinates
            global_pos  = target.mapToGlobal(QPoint(0, 0))
            window_pos  = self.window.mapFromGlobal(global_pos)
            target_rect = QRect(window_pos, target.size())

            self.overlay.set_spotlight(target_rect)
            self._position_card(target_rect)
        else:
            # Widget not found — center the card, no spotlight
            self.overlay.set_spotlight(QRect())
            self._center_card()

        self.card.update_step(index, step)
        self.card.raise_()

    def _position_card(self, target_rect: QRect):
        """
        Auto-position card to the side with the most available space,
        ensuring the card never overlaps the spotlight widget.
        """
        win_w = self.window.width()
        win_h = self.window.height()
        cw    = self.card.sizeHint().width()  or CARD_WIDTH
        ch    = self.card.sizeHint().height() or CARD_HEIGHT

        tr = target_rect

        # Available space in each direction (must fit the full card)
        space = {
            "above": tr.top()             - PADDING,
            "below": win_h - tr.bottom()  - PADDING,
            "left":  tr.left()            - PADDING,
            "right": win_w - tr.right()   - PADDING,
        }

        # Only consider directions where the card actually fits
        fits = {k: v for k, v in space.items() if v >= (ch if k in ("above", "below") else cw)}

        # Pick the direction with most room; fall back to largest space if none fit
        best = max(fits, key=fits.get) if fits else max(space, key=space.get)

        def clamp_x(x): return max(0, min(x, win_w - cw))
        def clamp_y(y): return max(0, min(y, win_h - ch))

        if best == "above":
            # If target is in the right half, anchor card to left side of window
            if tr.center().x() > win_w // 2:
                x = PADDING
            else:
                x = clamp_x(tr.center().x() - cw // 2)
            y = tr.top() - ch - PADDING
        elif best == "below":
            if tr.center().x() > win_w // 2:
                x = PADDING
            else:
                x = clamp_x(tr.center().x() - cw // 2)
            y = tr.bottom() + PADDING
        elif best == "left":
            x = tr.left() - cw - PADDING
            y = clamp_y(tr.center().y() - ch // 2)
        else:  # right
            x = tr.right() + PADDING
            y = clamp_y(tr.center().y() - ch // 2)

        # Final safety clamp
        x = max(0, min(x, win_w - cw))
        y = max(0, min(y, win_h - ch))

        self.card.move(x, y)

    def _center_card(self):
        cw = CARD_WIDTH
        ch = CARD_HEIGHT
        x  = (self.window.width()  - cw) // 2
        y  = (self.window.height() - ch) // 2
        self.card.move(x, y)

    def _next(self):
        if self.step_idx < len(STEPS) - 1:
            self._show_step(self.step_idx + 1)
        else:
            self._finish()

    def _back(self):
        if self.step_idx > 0:
            self._show_step(self.step_idx - 1)

    def _finish(self):
        mark_onboarding_complete()
        self._cleanup()

        # Confetti burst
        self._confetti = ConfettiOverlay(self.window, count=160)

        # Reminder dialog (slight delay so confetti is visible first)
        QTimer.singleShot(600, self._show_finish_dialog)

    def _skip(self):
        mark_onboarding_complete()
        self._cleanup()
        self._show_skip_dialog()

    def _show_finish_dialog(self):
        msg = QMessageBox(self.window)
        msg.setWindowTitle("🎉 You're all set!")
        msg.setText(
            "<b>Tutorial complete!</b><br><br>"
            "You can replay this tutorial any time from:<br>"
            "<b>Help → Show Tutorial</b>"
        )
        msg.setIcon(QMessageBox.Icon.NoIcon)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _show_skip_dialog(self):
        msg = QMessageBox(self.window)
        msg.setWindowTitle("Tutorial Skipped")
        msg.setText(
            "No problem! You can replay this tutorial any time from:<br>"
            "<b>Help → Show Tutorial</b>"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _cleanup(self):
        if self.overlay:
            self.overlay.hide()
            self.overlay.deleteLater()
            self.overlay = None
        if self.card:
            self.card.hide()
            self.card.deleteLater()
            self.card = None