# app/ui/ats_panel.py
"""
ATS Score Breakdown Panel — JobFit Pro
----------------------------------------

A right-side drawer panel that slides over the Tailor tab (75% width).
Contains:
  - Overall match score gauge
  - AI Detection score + deep analysis button
  - Section-by-section scores
  - Matched keywords (green chips)
  - Missing keywords (red chips) + suggestions
  - Keyword frequency bars
  - Actionable suggestions

Drawer pull tab on left edge toggles open/closed.
Auto-opens after first tailor; respects manual close.
"""

import re
from collections import Counter

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QProgressBar,
    QGridLayout,
    QApplication,
)
from PyQt6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QSize,
    QThread,
    pyqtSignal,
    QByteArray,
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPainterPath

from core.processor.keyword_analyzer import analyze_keywords
from core.processor.ai_detector import heuristic_score, deep_analysis


PANEL_WIDTH_RATIO = 0.75
PULL_TAB_WIDTH = 22
ANIM_DURATION = 280


# ==================================================================
# Keyword Analysis Worker (OpenAI)
# ==================================================================
class KeywordAnalysisWorker(QThread):
    """Runs OpenAI keyword analysis in background so panel opens instantly."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, job_text: str, resume_text: str):
        super().__init__()
        self.job_text = job_text
        self.resume_text = resume_text

    def run(self):
        try:
            result = analyze_keywords(self.job_text, self.resume_text)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ==================================================================
# Deep AI Analysis Worker
# ==================================================================
class DeepAnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            result = deep_analysis(self.text)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ==================================================================
# Drawer Pull Tab
# ==================================================================
class DrawerPullTab(QWidget):
    """Floating vertical pill that sits just outside the panel's left edge."""

    clicked = pyqtSignal()

    PILL_W = PULL_TAB_WIDTH
    PILL_H = 80

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.PILL_W, self.PILL_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_open(self, is_open: bool):
        self._open = is_open
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Pill background (full widget area)
        path = QPainterPath()
        path.addRoundedRect(1, 1, w - 2, h - 2, 7, 7)
        p.fillPath(path, QColor("#54AED5"))

        # Chevron arrow
        p.setPen(
            QPen(
                QColor("#0C1117"),
                2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        cx = w // 2
        cy = h // 2
        arm = 6
        if self._open:
            # > (panel is open, click to close — point right)
            p.drawLine(cx - arm // 2, cy - arm, cx + arm // 2, cy)
            p.drawLine(cx - arm // 2, cy + arm, cx + arm // 2, cy)
        else:
            # < (panel is closed, click to open — point left)
            p.drawLine(cx + arm // 2, cy - arm, cx - arm // 2, cy)
            p.drawLine(cx + arm // 2, cy + arm, cx - arm // 2, cy)

        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ==================================================================
# Score Gauge Widget
# ==================================================================
class ScoreGauge(QWidget):
    """Circular arc gauge showing a 0-100 score."""

    def __init__(self, label: str = "", size: int = 120, parent=None):
        super().__init__(parent)
        self._score = 0
        self._label = label
        self._size = size
        self.setFixedSize(size, size)

    def set_score(self, score: int):
        self._score = max(0, min(score, 100))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = self._size
        margin = 12
        rect = QRect(margin, margin, s - margin * 2, s - margin * 2)

        # Track arc
        p.setPen(
            QPen(QColor("#1E293B"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, 225 * 16, -270 * 16)

        # Score color
        if self._score >= 75:
            color = QColor("#34D399")
        elif self._score >= 50:
            color = QColor("#FBBF24")
        else:
            color = QColor("#F87171")

        # Score arc
        span = int(-270 * 16 * self._score / 100)
        p.setPen(QPen(color, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 225 * 16, span)

        # Score text
        p.setPen(QPen(QColor("#FFFFFF")))
        font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._score}%")

        # Label below
        if self._label:
            lbl_rect = QRect(0, s - 20, s, 18)
            p.setPen(QPen(QColor("#64748B")))
            font2 = QFont("Segoe UI", 8)
            p.setFont(font2)
            p.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, self._label)

        p.end()


# ==================================================================
# Keyword Chip
# ==================================================================
def _chip(text: str, color: str, bg: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"""
        QLabel {{
            background-color: {bg};
            color: {color};
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 9pt;
            font-weight: 600;
        }}
        QToolTip {{
            background-color: #1E293B;
            color: #F1F5F9;
            border: 1px solid #54AED5;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 9pt;
            font-weight: 400;
        }}
    """
    )
    lbl.setFixedHeight(22)
    return lbl


# ==================================================================
# Mini frequency bar
# ==================================================================
class FreqBar(QWidget):
    def __init__(self, word: str, count: int, max_count: int, parent=None):
        super().__init__(parent)
        self._word = word
        self._count = count
        self._max_count = max(max_count, 1)
        self.setFixedHeight(24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()

        label_w = 200
        count_w = 32
        bar_w = max(w - label_w - count_w - 8, 40)
        fill = int(bar_w * self._count / self._max_count)

        # Word label
        p.setPen(QPen(QColor("#CBD5E1")))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(
            QRect(0, 0, label_w, 24),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._word,
        )

        # Bar background
        p.fillRect(label_w + 4, 6, bar_w, 12, QColor("#1E293B"))

        # Bar fill
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(label_w + 4, 6, fill, 12, 4, 4)
        p.fillPath(path, QColor("#54AED5"))

        # Count
        p.setPen(QPen(QColor("#64748B")))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(
            QRect(label_w + 4 + bar_w + 4, 0, count_w, 24),
            Qt.AlignmentFlag.AlignVCenter,
            str(self._count),
        )
        p.end()


# ==================================================================
# Main ATS Panel
# ==================================================================
class ATSPanel(QWidget):
    """
    Sliding right-side drawer overlay.
    Parent must be the TailorTab (or any full-size content widget).
    """

    # Emits (ats_score: int) when OpenAI analysis completes
    analysisReady = pyqtSignal(int)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._is_open = False
        self._tailored_text = ""
        self._job_text = ""
        self._deep_worker = None
        self._kw_worker = None

        self._build_ui()
        self._create_pull_tab()  # pull tab parented to parent widget, must come before _build_animation
        self._build_animation()

        # Start fully hidden — only becomes visible after load() is called
        self.hide()

    # ----------------------------------------------------------
    # Build UI
    # ----------------------------------------------------------
    def _build_ui(self):
        self.setObjectName("atsPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            """
            QWidget#atsPanel {
                background-color: #0F172A;
                border-left: 1px solid #1E293B;
            }
            QToolTip {
                background-color: #1E293B;
                color: #F1F5F9;
                border: 1px solid #54AED5;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9pt;
            }
        """
        )

        # Root: scrollable content only (pull tab is a separate sibling widget)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Scrollable content ────────────────────────────────
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(scroll, stretch=1)

        # ── Pull tab lives on the PARENT, not inside the panel ──
        # Created after parent is known; see _create_pull_tab()
        self.pull_tab = None

        content = QWidget()
        content.setStyleSheet("background-color: #0F172A;")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(20, 20, 20, 20)
        self._content_layout.setSpacing(20)
        scroll.setWidget(content)

        # ── Header ────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("ATS Score Breakdown")
        title.setStyleSheet("color: #FFFFFF; font-size: 14pt; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(
            """
            QPushButton {
                background: #1E293B; color: #FFFFFF;
                border-radius: 14px; font-size: 10pt;
            }
            QPushButton:hover { background: #334155; }
        """
        )
        btn_close.clicked.connect(self.close_panel)
        header.addWidget(btn_close)
        self._content_layout.addLayout(header)

        # ── Overall + AI gauges row ───────────────────────────
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(32)

        self.gauge_ats = ScoreGauge("ATS Match", 130)
        self.gauge_ai = ScoreGauge("AI Detection", 130)

        ats_col = QVBoxLayout()
        ats_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ats_col.addWidget(self.gauge_ats, alignment=Qt.AlignmentFlag.AlignCenter)
        ats_lbl = QLabel("Keyword Match Score")
        ats_lbl.setStyleSheet("color: #94A3B8; font-size: 9pt;")
        ats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ats_col.addWidget(ats_lbl)

        ai_col = QVBoxLayout()
        ai_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_col.addWidget(self.gauge_ai, alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_ai_verdict = QLabel("Heuristic score")
        self.lbl_ai_verdict.setStyleSheet("color: #94A3B8; font-size: 9pt;")
        self.lbl_ai_verdict.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_col.addWidget(self.lbl_ai_verdict)

        self.btn_deep = QPushButton("🔍 Run Deep AI Analysis")
        self.btn_deep.setStyleSheet(
            """
            QPushButton {
                background-color: #1E293B;
                color: #54AED5;
                border: 1px solid #54AED5;
                border-radius: 6px;
                padding: 5px 14px;
                font-size: 9pt;
            }
            QPushButton:hover { background-color: #273549; }
            QPushButton:disabled { color: #334155; border-color: #334155; }
        """
        )
        self.btn_deep.clicked.connect(self._run_deep_analysis)
        ai_col.addWidget(self.btn_deep, alignment=Qt.AlignmentFlag.AlignCenter)

        gauges_row.addStretch()
        gauges_row.addLayout(ats_col)
        gauges_row.addLayout(ai_col)
        gauges_row.addStretch()
        self._content_layout.addLayout(gauges_row)

        self._add_divider()

        # ── Section scores ────────────────────────────────────
        self._section_container = self._add_section("Section Scores")
        self._section_grid = QGridLayout()
        self._section_grid.setSpacing(8)
        self._section_container.addLayout(self._section_grid)

        self._add_divider()

        # ── AI signals ────────────────────────────────────────
        self._ai_signals_container = self._add_section("AI Writing Signals")

        self._add_divider()

        # ── Integrity check (fabrication warnings) ────────────
        self._fabrication_container = self._add_section("🔒 Integrity Check")

        self._add_divider()

        # ── Matched keywords ──────────────────────────────────
        self._matched_container = self._add_section("✅ Matched Keywords")

        self._add_divider()

        # ── Suggested keyword additions ───────────────────────
        self._missing_container = self._add_section("💡 Suggested Keyword Additions")

        self._add_divider()

        # ── Frequency breakdown ───────────────────────────────
        self._freq_container = self._add_section("Keyword Frequency")

        self._add_divider()

        # ── Suggestions ───────────────────────────────────────
        self._suggestions_container = self._add_section("💡 Actionable Suggestions")

        self._content_layout.addStretch()

    def _add_section(self, title: str) -> QVBoxLayout:
        lbl = QLabel(title)
        lbl.setStyleSheet(
            "color: #54AED5; font-size: 10pt; font-weight: 700; margin-bottom: 4px;"
        )
        self._content_layout.addWidget(lbl)
        container = QVBoxLayout()
        container.setSpacing(6)
        self._content_layout.addLayout(container)
        return container

    def _add_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1E293B;")
        self._content_layout.addWidget(line)

    # ----------------------------------------------------------
    # Animation
    # ----------------------------------------------------------
    def _build_animation(self):
        self._anim = QPropertyAnimation(self, QByteArray(b"geometry"))
        self._anim.setDuration(ANIM_DURATION)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Animation for pull tab (also on parent)
        self._tab_anim = QPropertyAnimation(self.pull_tab, QByteArray(b"geometry"))
        self._tab_anim.setDuration(ANIM_DURATION)
        self._tab_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _create_pull_tab(self):
        """Create pull tab as sibling of panel on the parent widget."""
        self.pull_tab = DrawerPullTab(self.parent())
        self.pull_tab.clicked.connect(self.toggle)
        self.pull_tab.hide()  # hidden until first load()

    def _panel_rect_open(self) -> QRect:
        pw = self.parent().width()
        ph = self.parent().height()
        w = int(pw * PANEL_WIDTH_RATIO)
        return QRect(pw - w, 0, w, ph)

    def _panel_rect_closed(self) -> QRect:
        """Panel slides fully off the right edge."""
        pw = self.parent().width()
        ph = self.parent().height()
        w = int(pw * PANEL_WIDTH_RATIO)
        return QRect(pw, 0, w, ph)

    def _pull_tab_rect_open(self) -> QRect:
        """Pull tab sits just outside the left edge of the open panel."""
        pw = self.parent().width()
        ph = self.parent().height()
        panel_x = pw - int(pw * PANEL_WIDTH_RATIO)
        tab_h = 80
        tab_y = (ph - tab_h) // 2
        return QRect(panel_x - PULL_TAB_WIDTH - 4, tab_y, PULL_TAB_WIDTH, tab_h)

    def _pull_tab_rect_closed(self) -> QRect:
        """Pull tab sits at the right edge when panel is closed."""
        pw = self.parent().width()
        ph = self.parent().height()
        tab_h = 80
        tab_y = (ph - tab_h) // 2
        return QRect(pw - PULL_TAB_WIDTH - 4, tab_y, PULL_TAB_WIDTH, tab_h)

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------
    def load(self, job_text: str, tailored_text: str):
        """Open panel immediately with AI detection results, then load keyword analysis async."""
        self._job_text = job_text
        self._tailored_text = tailored_text

        # Run heuristic AI detection instantly (no network call)
        ai = heuristic_score(tailored_text)
        self._show_ai_results(ai)
        self._show_loading_state()

        # Show panel and pull tab for the first time if hidden
        if not self.isVisible():
            self.setGeometry(self._panel_rect_closed())
            self.show()
            self.pull_tab.setGeometry(self._pull_tab_rect_closed())
            self.pull_tab.show()
            self.pull_tab.raise_()

        # Force open
        self._is_open = False
        self.open_panel()

        # Fire OpenAI keyword analysis in background
        self._kw_worker = KeywordAnalysisWorker(job_text, tailored_text)
        self._kw_worker.finished.connect(self._on_keyword_analysis_done)
        self._kw_worker.error.connect(self._on_keyword_analysis_error)
        self._kw_worker.start()

    def open_panel(self):
        if self._is_open:
            return
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(self._panel_rect_open())
        self._anim.start()
        self._tab_anim.stop()
        self._tab_anim.setStartValue(self.pull_tab.geometry())
        self._tab_anim.setEndValue(self._pull_tab_rect_open())
        self._tab_anim.start()
        self._is_open = True
        self.pull_tab.set_open(True)

    def close_panel(self):
        if not self._is_open:
            return
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(self._panel_rect_closed())
        self._anim.start()
        self._tab_anim.stop()
        self._tab_anim.setStartValue(self.pull_tab.geometry())
        self._tab_anim.setEndValue(self._pull_tab_rect_closed())
        self._tab_anim.start()
        self._is_open = False
        self.pull_tab.set_open(False)

    def toggle(self):
        if self._is_open:
            self.close_panel()
        else:
            self.open_panel()

    def auto_open(self):
        """Kept for API compatibility."""
        self.open_panel()

    # ----------------------------------------------------------
    # Layout helper
    # ----------------------------------------------------------
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    # ----------------------------------------------------------
    # Immediate display: AI heuristic results + loading placeholders
    # ----------------------------------------------------------
    def _show_ai_results(self, ai: dict):
        """Populate AI detection gauge and signals immediately."""
        self.gauge_ai.set_score(ai["score"])
        score = ai["score"]
        if score < 30:
            verdict, color = "Likely Human ✅", "#34D399"
        elif score < 60:
            verdict, color = "Possibly AI-Assisted ⚠️", "#FBBF24"
        else:
            verdict, color = "Likely AI-Generated 🤖", "#F87171"
        self.lbl_ai_verdict.setText(verdict)
        self.lbl_ai_verdict.setStyleSheet(
            f"color: {color}; font-size: 9pt; font-weight: 600;"
        )

        self._clear_layout(self._ai_signals_container)
        for sig in ai.get("signals", []):
            lbl = QLabel(f"• {sig}")
            lbl.setStyleSheet("color: #CBD5E1; font-size: 9pt;")
            lbl.setWordWrap(True)
            self._ai_signals_container.addWidget(lbl)

    def _show_loading_state(self):
        """Show spinners/placeholders while OpenAI keyword analysis runs."""
        self.gauge_ats.set_score(0)

        # Clear section grid
        while self._section_grid.count():
            item = self._section_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loading_lbl = QLabel("⏳ Analyzing with AI...")
        loading_lbl.setStyleSheet("color: #54AED5; font-size: 9pt; font-style: italic;")
        self._section_grid.addWidget(loading_lbl, 0, 0, 1, 3)

        for container in (
            self._matched_container,
            self._missing_container,
            self._freq_container,
            self._suggestions_container,
            self._fabrication_container,
        ):
            self._clear_layout(container)
            lbl = QLabel("⏳ Loading...")
            lbl.setStyleSheet("color: #475569; font-size: 9pt; font-style: italic;")
            container.addWidget(lbl)

    # ----------------------------------------------------------
    # OpenAI keyword analysis callback
    # ----------------------------------------------------------
    def _on_keyword_analysis_done(self, result: dict):
        if result.get("error"):
            self._show_analysis_error(result["error"])
            return

        # ATS score gauge
        self.gauge_ats.set_score(result["ats_score"])

        # Section scores
        self._populate_sections_from_ai(result.get("section_scores", {}))

        # Matched keywords
        self._clear_layout(self._matched_container)
        matched = result.get("matched_keywords", [])
        if matched:
            wrap = QWidget()
            flow = _FlowLayout(wrap)
            for item in matched:
                kw = item.get("keyword", "") if isinstance(item, dict) else str(item)
                ctx = item.get("context", "") if isinstance(item, dict) else ""
                chip = _chip(kw, "#FFFFFF", "#166534")
                if ctx:
                    chip.setToolTip(ctx)
                flow.addWidget(chip)
            self._matched_container.addWidget(wrap)
        else:
            self._matched_container.addWidget(QLabel("No matched keywords found."))

        # Suggested additions
        self._clear_layout(self._missing_container)
        suggestions = result.get("suggested_additions", [])
        if suggestions:
            wrap = QWidget()
            flow = _FlowLayout(wrap)
            for item in suggestions:
                kw = item.get("keyword", "") if isinstance(item, dict) else str(item)
                reason = item.get("reason", "") if isinstance(item, dict) else ""
                conf = (
                    item.get("confidence", "medium")
                    if isinstance(item, dict)
                    else "medium"
                )
                bg = {"high": "#7C2D12", "medium": "#7F1D1D", "low": "#450A0A"}.get(
                    conf, "#7F1D1D"
                )
                chip = _chip(kw, "#FFFFFF", bg)
                if reason:
                    chip.setToolTip(f"{reason}\nConfidence: {conf}")
                flow.addWidget(chip)
            self._missing_container.addWidget(wrap)

            note = QLabel(
                "💡 Hover a chip to see why it's suggested. Only add skills you genuinely have."
            )
            note.setStyleSheet("color: #64748B; font-size: 8pt; font-style: italic;")
            note.setWordWrap(True)
            self._missing_container.addWidget(note)
        else:
            self._missing_container.addWidget(
                QLabel("No additional keywords suggested — great coverage!")
            )

        # Fabrication warnings
        self._clear_layout(self._fabrication_container)
        warnings = result.get("fabrication_warnings", [])
        if warnings:
            for w in warnings:
                item_text = w.get("item", "") if isinstance(w, dict) else str(w)
                reason = w.get("reason", "") if isinstance(w, dict) else ""
                lbl = QLabel(f"⚠️ {item_text}")
                lbl.setStyleSheet("color: #F87171; font-size: 9pt; font-weight: 600;")
                lbl.setWordWrap(True)
                if reason:
                    lbl.setToolTip(reason)
                self._fabrication_container.addWidget(lbl)
                if reason:
                    sub = QLabel(f"   {reason}")
                    sub.setStyleSheet("color: #94A3B8; font-size: 8pt;")
                    sub.setWordWrap(True)
                    self._fabrication_container.addWidget(sub)
        else:
            ok = QLabel("✅ No fabricated skills or experiences detected.")
            ok.setStyleSheet("color: #34D399; font-size: 9pt;")
            self._fabrication_container.addWidget(ok)

        # Frequency bars — top keywords from matched list
        self._clear_layout(self._freq_container)
        if matched:
            top = matched[:10]
            for i, item in enumerate(top):
                kw = item.get("keyword", "") if isinstance(item, dict) else str(item)
                bar = FreqBar(kw, len(top) - i, len(top))
                self._freq_container.addWidget(bar)

        # Actionable suggestions
        self._clear_layout(self._suggestions_container)
        ai_result = {
            "score": self.gauge_ai._score,
            "ai_phrases_found": [],
            "passive_voice_count": 0,
        }
        self._build_suggestions_from_ai(result, ai_result)

        # Store full result so history tab can replay it later
        self._last_analysis = result

        # Notify listeners (window_main → toast + badge)
        self.analysisReady.emit(int(result.get("ats_score", 0)))

    def load_from_history(self, result: dict):
        """
        Replay a stored ATS analysis result (from history JSON).
        Opens the panel and populates all sections without making any API call.
        """
        if not result:
            return

        # Show / open panel
        if not self.isVisible():
            self.setGeometry(self._panel_rect_closed())
            self.show()
            self.pull_tab.setGeometry(self._pull_tab_rect_closed())
            self.pull_tab.show()
            self.pull_tab.raise_()

        self._is_open = False
        self.open_panel()

        # Populate with stored data — reuse the same rendering path
        self._on_keyword_analysis_done(result)

    def _on_keyword_analysis_error(self, error: str):
        self._show_analysis_error(error)

    def _show_analysis_error(self, error: str):
        for container in (
            self._matched_container,
            self._missing_container,
            self._suggestions_container,
        ):
            self._clear_layout(container)
        lbl = QLabel(f"⚠️ Analysis failed: {error}")
        lbl.setStyleSheet("color: #F87171; font-size: 9pt;")
        lbl.setWordWrap(True)
        self._suggestions_container.addWidget(lbl)

    def _populate_sections_from_ai(self, section_scores: dict):
        """Render section score bars from OpenAI-provided scores."""
        while self._section_grid.count():
            item = self._section_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row = 0
        for section, score in section_scores.items():
            if score is None:
                continue  # section absent — skip

            name_lbl = QLabel(section)
            name_lbl.setStyleSheet("color: #CBD5E1; font-size: 9pt;")

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(score))
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            color = (
                "#34D399" if score >= 70 else "#FBBF24" if score >= 40 else "#F87171"
            )
            bar.setStyleSheet(
                f"""
                QProgressBar {{ background-color: #1E293B; border-radius: 5px; }}
                QProgressBar::chunk {{ background-color: {color}; border-radius: 5px; }}
            """
            )

            score_lbl = QLabel(f"{int(score)}%")
            score_lbl.setStyleSheet(
                f"color: {color}; font-size: 9pt; font-weight: 600;"
            )
            score_lbl.setFixedWidth(36)

            self._section_grid.addWidget(name_lbl, row, 0)
            self._section_grid.addWidget(bar, row, 1)
            self._section_grid.addWidget(score_lbl, row, 2)
            row += 1

        self._section_grid.setColumnStretch(1, 1)

    def _build_suggestions_from_ai(self, kw_result: dict, ai: dict):
        """Build actionable suggestions from OpenAI keyword result + AI heuristic."""
        suggestions = []
        score = kw_result.get("ats_score", 0)
        summary = kw_result.get("summary", "")

        if summary:
            suggestions.append(summary)

        if score < 50:
            suggestions.append(
                "Your ATS match score is low. Re-tailor with 'Emphasize job keywords' enabled."
            )
        elif score < 75:
            suggestions.append(
                "Good match but room to improve. Review suggested keywords above and add any you have."
            )

        if kw_result.get("fabrication_warnings"):
            suggestions.append(
                "⚠️ Potential fabricated content detected — review the Integrity Check section above "
                "and ensure all listed skills accurately reflect your background."
            )

        ai_score = ai.get("score", 0)
        if ai_score >= 60:
            suggestions.append(
                "Your resume scored high for AI-generated language. "
                "Run Deep AI Analysis below for specific humanization tips."
            )
        elif ai_score >= 30:
            suggestions.append(
                "Some AI-associated phrases detected. Replace buzzwords with "
                "specific metrics and personal achievements."
            )

        if not suggestions:
            suggestions.append(
                "Strong match! Consider quantifying achievements with numbers and percentages "
                "to stand out further."
            )

        for sug in suggestions:
            lbl = QLabel(f"→ {sug}")
            lbl.setStyleSheet("color: #CBD5E1; font-size: 9pt; padding: 2px 0;")
            lbl.setWordWrap(True)
            self._suggestions_container.addWidget(lbl)

    # ----------------------------------------------------------
    # Deep Analysis
    # ----------------------------------------------------------
    def _run_deep_analysis(self):
        if not self._tailored_text:
            return

        self.btn_deep.setEnabled(False)
        self.btn_deep.setText("⏳ Analyzing...")

        self._deep_worker = DeepAnalysisWorker(self._tailored_text)
        self._deep_worker.finished.connect(self._on_deep_done)
        self._deep_worker.error.connect(self._on_deep_error)
        self._deep_worker.start()

    def _on_deep_done(self, result: dict):
        self.btn_deep.setEnabled(True)
        self.btn_deep.setText("🔍 Run Deep AI Analysis")

        score = result.get("score", -1)
        if score >= 0:
            self.gauge_ai.set_score(score)

        verdict = result.get("verdict", "Unknown")
        self.lbl_ai_verdict.setText(f"{verdict} (Deep)")

        # Append deep suggestions
        suggestions = result.get("suggestions", [])
        if suggestions:
            divider_lbl = QLabel("— Deep Analysis Suggestions —")
            divider_lbl.setStyleSheet(
                "color: #54AED5; font-size: 9pt; font-weight: 600; margin-top: 8px;"
            )
            self._suggestions_container.addWidget(divider_lbl)

            for sug in suggestions:
                lbl = QLabel(f"→ {sug}")
                lbl.setStyleSheet("color: #CBD5E1; font-size: 9pt; padding: 2px 0;")
                lbl.setWordWrap(True)
                self._suggestions_container.addWidget(lbl)

    def _on_deep_error(self, error: str):
        self.btn_deep.setEnabled(True)
        self.btn_deep.setText("🔍 Run Deep AI Analysis")
        lbl = QLabel(f"Deep analysis failed: {error}")
        lbl.setStyleSheet("color: #F87171; font-size: 9pt;")
        self._suggestions_container.addWidget(lbl)

    # ----------------------------------------------------------
    # Resize with parent
    # ----------------------------------------------------------
    def reposition(self):
        """Call when parent resizes to keep panel and pull tab correctly positioned."""
        if not self.isVisible():
            return
        if self._is_open:
            self.setGeometry(self._panel_rect_open())
            self.pull_tab.setGeometry(self._pull_tab_rect_open())
        else:
            self.setGeometry(self._panel_rect_closed())
            self.pull_tab.setGeometry(self._pull_tab_rect_closed())
        self.pull_tab.raise_()


# ==================================================================
# Simple Flow Layout for keyword chips
# ==================================================================
class _FlowLayout(object):
    """Minimal horizontal-wrapping layout for chip widgets."""

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._widgets: list = []
        self._layout = _WrapLayout(parent)

    def addWidget(self, widget: QWidget):
        self._layout.addWidget(widget)


class _WrapLayout(QVBoxLayout):
    """Wraps chips into rows."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(4)
        self._current_row: QHBoxLayout | None = None
        self._row_width = 0

    def addWidget(self, widget: QWidget):
        widget.setParent(self.parentWidget())
        widget.show()
        widget.adjustSize()
        chip_w = widget.sizeHint().width() + 8

        max_w = (self.parentWidget().width() or 400) - 10

        if self._current_row is None or self._row_width + chip_w > max_w:
            self._current_row = QHBoxLayout()
            self._current_row.setSpacing(4)
            self._current_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
            super().addLayout(self._current_row)
            self._row_width = 0

        self._current_row.addWidget(widget)
        self._row_width += chip_w
