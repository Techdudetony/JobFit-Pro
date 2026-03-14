"""
TailorContextDialog
--------------------

A pre-tailor modal that displays AI-generated, resume-specific clarifying
questions before sending to the tailor engine. Questions are dynamic and
personalized to the user's resume + job description.

Question types supported:
  - "yes_no"          → 2-option radio buttons
  - "single_choice"   → radio button group (pick one)
  - "multiple_choice" → checkbox group (pick many)
  - "text"            → free-text QTextEdit

Usage:
    dialog = TailorContextDialog(questions, parent=self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        context = dialog.get_context()
        # pass to ResumeTailor.generate(context=context)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QTextEdit, QFrame, QSizePolicy, QWidget,
    QButtonGroup, QRadioButton, QCheckBox,
)
from PyQt6.QtCore import Qt


class TailorContextDialog(QDialog):

    def __init__(self, questions: list, parent=None):
        super().__init__(parent)
        self.setObjectName("TailorContextDialog")
        self.setWindowTitle("Before We Tailor...")
        self.setMinimumWidth(580)
        self.setMaximumWidth(680)
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._questions = questions
        self._widgets   = {}   # key → widget or list of widgets
        self._groups    = {}   # key → QButtonGroup (for radio types)

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 20)
        outer.setSpacing(14)

        # Header
        header = QLabel("Help us tailor your resume better")
        header.setProperty("panelTitle", True)
        outer.addWidget(header)

        sub = QLabel(
            "Answer as many questions as you like — leave any blank to skip. "
            "These answers are never stored."
        )
        sub.setWordWrap(True)
        sub.setProperty("subtitleLabel", True)
        outer.addWidget(sub)

        divider_top = QFrame()
        divider_top.setFrameShape(QFrame.Shape.HLine)
        divider_top.setObjectName("dialogDivider")
        outer.addWidget(divider_top)

        # Scrollable question area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("contextScroll")

        scroll_content = QWidget()
        scroll_content.setObjectName("contextScrollContent")
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        q_layout = QVBoxLayout(scroll_content)
        q_layout.setContentsMargins(4, 4, 4, 4)
        q_layout.setSpacing(18)

        for q in self._questions:
            self._add_question(q_layout, q)

        q_layout.addStretch()
        scroll.setWidget(scroll_content)

        # Constrain scroll height so dialog doesn't overflow screen
        scroll.setMinimumHeight(300)
        scroll.setMaximumHeight(480)
        outer.addWidget(scroll)

        divider_bot = QFrame()
        divider_bot.setFrameShape(QFrame.Shape.HLine)
        divider_bot.setObjectName("dialogDivider")
        outer.addWidget(divider_bot)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_skip = QPushButton("Skip — Tailor Without Context")
        self.btn_skip.setProperty("panelButton", True)
        self.btn_skip.clicked.connect(self._on_skip)

        self.btn_tailor = QPushButton("Tailor Resume →")
        self.btn_tailor.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_skip)
        btn_row.addWidget(self.btn_tailor)
        outer.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _add_question(self, layout: QVBoxLayout, q: dict):
        q_type   = q.get("type", "text")
        key      = q.get("key", "unknown")
        question = q.get("question", "")
        options  = q.get("options", [])
        placeholder = q.get("placeholder", "")

        # Question label
        label = QLabel(question)
        label.setWordWrap(True)
        label.setProperty("questionLabel", True)
        layout.addWidget(label)

        # Instruction hint beneath the question
        if q_type in ("yes_no", "single_choice"):
            hint = QLabel("Choose one")
            hint.setProperty("subtitleLabel", True)
            layout.addWidget(hint)
        elif q_type == "multiple_choice":
            hint = QLabel("Select all that apply")
            hint.setProperty("subtitleLabel", True)
            layout.addWidget(hint)

        # ── yes/no + single_choice → radio buttons ──────────────────
        if q_type in ("yes_no", "single_choice"):
            group = QButtonGroup(self)
            self._groups[key] = group
            self._widgets[key] = group

            for opt in options:
                rb = QRadioButton(opt)
                rb.setProperty("contextOption", True)
                group.addButton(rb)
                layout.addWidget(rb)

        # ── multiple_choice → checkboxes ────────────────────────────
        elif q_type == "multiple_choice":
            checkboxes = []
            for opt in options:
                cb = QCheckBox(opt)
                cb.setProperty("contextOption", True)
                layout.addWidget(cb)
                checkboxes.append((opt, cb))
            self._widgets[key] = checkboxes

        # ── text → QTextEdit ────────────────────────────────────────
        else:
            te = QTextEdit()
            te.setPlaceholderText(placeholder or "Type your answer here...")
            te.setFixedHeight(72)
            te.setProperty("contextField", True)
            te.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(te)
            self._widgets[key] = te

        # Optional clarification expander
        clarify_key = f"{key}_clarification"

        clarify_toggle = QPushButton("+ Add a clarification or note")
        clarify_toggle.setProperty("clarifyToggle", True)
        clarify_toggle.setFlat(True)
        layout.addWidget(clarify_toggle)

        clarify_box = QTextEdit()
        clarify_box.setPlaceholderText(
            "e.g. I no longer work there — this was a past role ending Nov 2025..."
        )
        clarify_box.setFixedHeight(60)
        clarify_box.setProperty("contextField", True)
        clarify_box.setVisible(False)
        layout.addWidget(clarify_box)
        self._widgets[clarify_key] = clarify_box

        # Toggle visibility on click
        def _toggle(checked, box=clarify_box, btn=clarify_toggle):
            visible = not box.isVisible()
            box.setVisible(visible)
            btn.setText("− Remove note" if visible else "+ Add a clarification or note")

        clarify_toggle.clicked.connect(_toggle)

        # Light separator between questions
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("questionSeparator")
        layout.addWidget(sep)

    # ------------------------------------------------------------------
    def _on_skip(self):
        self._widgets.clear()
        self._groups.clear()
        self.accept()

    # ------------------------------------------------------------------
    def get_context(self) -> str:
        """
        Compile all answered questions into a formatted context string
        for injection into the tailor prompt. Skips unanswered fields.
        """
        parts = []

        for q in self._questions:
            key    = q.get("key", "")
            q_type = q.get("type", "text")
            label  = q.get("question", key)
            widget = self._widgets.get(key)

            if widget is None:
                continue

            if q_type in ("yes_no", "single_choice"):
                checked = widget.checkedButton()
                if checked:
                    parts.append(f"{label}: {checked.text()}")

            elif q_type == "multiple_choice":
                selected = [opt for opt, cb in widget if cb.isChecked()]
                if selected:
                    parts.append(f"{label}: {', '.join(selected)}")

            else:
                text = widget.toPlainText().strip()
                if text:
                    parts.append(f"{label}: {text}")

            # Append clarification note if the user expanded and filled it
            clarify_widget = self._widgets.get(f"{key}_clarification")
            if clarify_widget:
                note = clarify_widget.toPlainText().strip()
                if note:
                    parts.append(f"  → Candidate clarification: {note}")

        return "\n".join(parts)