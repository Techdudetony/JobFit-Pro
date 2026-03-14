"""
Tab: Resume Builder — JobFit Pro
----------------------------------

5th sidebar tab. Three entry points:
  - New Resume (blank form)
  - Import Resume (PDF/DOCX → pre-filled form)
  - Use Tailored Resume (session tailored text → pre-filled form)

Layout:
  Left  — scrollable section cards (Personal Info, Summary, Experience, etc.)
  Right — live styled preview (renders via ResumeStyleEngine, debounced 500ms)

AI assist per section via ResumeBuilderAI.
Export via ResumeStyleEngine (respects selected style from Settings).
"""

import os
import json

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QScrollArea, QLabel, QPushButton, QLineEdit,
    QTextEdit, QGroupBox, QFormLayout, QComboBox,
    QCheckBox, QFrame, QFileDialog, QMessageBox,
    QSizePolicy, QHBoxLayout,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from app.ui.tabs.resume_data import ResumeData, WorkEntry, EducationEntry
from app.ui.tabs.resume_data import SkillEntry, ProjectEntry, CertificationEntry
from app.ui.tabs.resume_builder_ai import ResumeBuilderAI


# ── Helpers ──────────────────────────────────────────────────────────────────
def _divider():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setObjectName("builderDivider")
    return f


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("builderSectionTitle", True)
    return lbl


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("builderFieldLabel", True)
    return lbl


def _ai_btn(tooltip: str = "Improve with AI") -> QPushButton:
    btn = QPushButton("✨ Improve")
    btn.setProperty("aiImproveBtn", True)
    btn.setToolTip(tooltip)
    btn.setFixedHeight(26)
    return btn


# ── Single work experience card ──────────────────────────────────────────────
class _WorkCard(QGroupBox):
    changed  = pyqtSignal()
    removed  = pyqtSignal(object)   # emits self

    def __init__(self, entry: WorkEntry = None, parent=None):
        super().__init__(parent)
        self.setObjectName("builderCard")
        self._entry = entry or WorkEntry()
        self._ai    = ResumeBuilderAI()
        self._worker = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Row 1: title + company
        row1 = QHBoxLayout()
        self.inp_title   = QLineEdit(); self.inp_title.setPlaceholderText("Job Title")
        self.inp_company = QLineEdit(); self.inp_company.setPlaceholderText("Company")
        row1.addWidget(self.inp_title, 2)
        row1.addWidget(self.inp_company, 2)
        layout.addLayout(row1)

        # Row 2: location + dates
        row2 = QHBoxLayout()
        self.inp_location   = QLineEdit(); self.inp_location.setPlaceholderText("Location")
        self.inp_start      = QLineEdit(); self.inp_start.setPlaceholderText("Start (e.g. Jan 2020)")
        self.inp_end        = QLineEdit(); self.inp_end.setPlaceholderText("End (or Present)")
        self.chk_current    = QCheckBox("Current")
        self.chk_current.toggled.connect(self._on_current_toggled)
        row2.addWidget(self.inp_location, 2)
        row2.addWidget(self.inp_start, 1)
        row2.addWidget(self.inp_end, 1)
        row2.addWidget(self.chk_current)
        layout.addLayout(row2)

        # Bullets
        bullets_header = QHBoxLayout()
        bullets_header.addWidget(_field_label("Bullet Points"))
        bullets_header.addStretch()
        self._ai_btn = _ai_btn("Improve bullet points with AI")
        self._ai_btn.clicked.connect(self._improve_bullets)
        bullets_header.addWidget(self._ai_btn)
        layout.addLayout(bullets_header)

        self.inp_bullets = QTextEdit()
        self.inp_bullets.setPlaceholderText(
            "- Led the design and rollout of...\n- Reduced X by Y% through...\n- Delivered Z on time and under budget..."
        )
        self.inp_bullets.setFixedHeight(120)
        self.inp_bullets.setObjectName("builderTextEdit")
        layout.addWidget(self.inp_bullets)

        # Remove button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_remove = QPushButton("Remove")
        btn_remove.setProperty("removeBtn", True)
        btn_remove.setFixedHeight(24)
        btn_remove.clicked.connect(lambda: self.removed.emit(self))
        btn_row.addWidget(btn_remove)
        layout.addLayout(btn_row)

        # Populate
        e = self._entry
        self.inp_title.setText(e.title)
        self.inp_company.setText(e.company)
        self.inp_location.setText(e.location)
        self.inp_start.setText(e.start_date)
        self.inp_end.setText(e.end_date)
        self.chk_current.setChecked(e.current)
        self.inp_bullets.setPlainText(e.bullets_text())

        # Wire changes
        for w in (self.inp_title, self.inp_company, self.inp_location,
                  self.inp_start, self.inp_end):
            w.textChanged.connect(self.changed)
        self.inp_bullets.textChanged.connect(self.changed)
        self.chk_current.toggled.connect(self.changed)

        self._update_title()
        self.inp_title.textChanged.connect(self._update_title)
        self.inp_company.textChanged.connect(self._update_title)

    def _on_current_toggled(self, checked: bool):
        """Make end date read-only with forbidden cursor when role is current."""
        from PyQt6.QtGui import QCursor
        from PyQt6.QtCore import Qt as _Qt
        # Use setReadOnly instead of setEnabled — disabled widgets ignore setCursor
        self.inp_end.setReadOnly(checked)
        if checked:
            self.inp_end.setText("")
            self.inp_end.setPlaceholderText("Present")
            self.inp_end.setCursor(QCursor(_Qt.CursorShape.ForbiddenCursor))
            self.inp_end.setProperty("fieldLocked", True)
        else:
            self.inp_end.setPlaceholderText("End (or Present)")
            self.inp_end.setCursor(QCursor(_Qt.CursorShape.IBeamCursor))
            self.inp_end.setProperty("fieldLocked", False)
        # Force QSS re-evaluation for locked style
        self.inp_end.style().unpolish(self.inp_end)
        self.inp_end.style().polish(self.inp_end)
        self.changed.emit()

    def _update_title(self):
        t = self.inp_title.text() or "New Role"
        c = self.inp_company.text()
        self.setTitle(f"  {t}{' @ ' + c if c else ''}")

    def _improve_bullets(self):
        bullets = self.inp_bullets.toPlainText().strip()
        if not bullets:
            QMessageBox.information(self, "Empty", "Add some bullet points first.")
            return
        self._ai_btn.setText("✨ Improving...")
        self._ai_btn.setEnabled(False)
        self._worker = self._ai.improve_bullets(
            bullets, self.inp_title.text(), self.inp_company.text()
        )
        self._worker.finished.connect(self._on_bullets_improved)
        self._worker.error.connect(lambda e: self._reset_ai_btn())
        self._worker.start()

    def _on_bullets_improved(self, text: str):
        self.inp_bullets.setPlainText(text)
        self._reset_ai_btn()

    def _reset_ai_btn(self):
        self._ai_btn.setText("✨ Improve")
        self._ai_btn.setEnabled(True)

    def get_entry(self) -> WorkEntry:
        e = WorkEntry()
        e.title      = self.inp_title.text().strip()
        e.company    = self.inp_company.text().strip()
        e.location   = self.inp_location.text().strip()
        e.start_date = self.inp_start.text().strip()
        e.end_date   = self.inp_end.text().strip()
        e.current    = self.chk_current.isChecked()
        e.set_bullets_from_text(self.inp_bullets.toPlainText())
        return e


# ── Single skill row ──────────────────────────────────────────────────────────
class _SkillRow(QWidget):
    changed = pyqtSignal()
    removed = pyqtSignal(object)

    def __init__(self, entry: SkillEntry = None, parent=None):
        super().__init__(parent)
        self._entry = entry or SkillEntry()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Skill name")
        self.inp_name.setText(self._entry.name)

        self.combo_level = QComboBox()
        self.combo_level.addItems(["Beginner", "Familiar", "Proficient", "Expert"])
        idx = self.combo_level.findText(self._entry.proficiency)
        if idx >= 0:
            self.combo_level.setCurrentIndex(idx)
        self.combo_level.setFixedWidth(110)

        btn_remove = QPushButton("✕")
        btn_remove.setProperty("removeBtn", True)
        btn_remove.setFixedSize(24, 24)
        btn_remove.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.inp_name, 3)
        layout.addWidget(self.combo_level)
        layout.addWidget(btn_remove)

        self.inp_name.textChanged.connect(self.changed)
        self.combo_level.currentTextChanged.connect(self.changed)

    def get_entry(self) -> SkillEntry:
        return SkillEntry(
            name=self.inp_name.text().strip(),
            proficiency=self.combo_level.currentText()
        )


# ── Main tab ─────────────────────────────────────────────────────────────────
class ResumeBuilderTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data    = ResumeData()
        self._ai      = ResumeBuilderAI()
        self._worker  = None
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(500)
        self._debounce.timeout.connect(self._refresh_preview)

        self._work_cards:  list[_WorkCard]  = []
        self._skill_rows:  list[_SkillRow]  = []

        self._build_ui()

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("builderSplitter")

        # ── LEFT: form panel ──
        left_widget = QWidget()
        left_widget.setObjectName("builderLeft")
        left_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Entry point buttons
        btn_bar = QWidget()
        btn_bar.setObjectName("builderBtnBar")
        btn_bar_layout = QHBoxLayout(btn_bar)
        btn_bar_layout.setContentsMargins(16, 12, 16, 12)
        btn_bar_layout.setSpacing(8)

        lbl_builder = QLabel("Resume Builder")
        lbl_builder.setProperty("panelTitle", True)
        btn_bar_layout.addWidget(lbl_builder)
        btn_bar_layout.addStretch()

        self.btn_new      = QPushButton("+ New")
        self.btn_import   = QPushButton("⬆ Import")
        self.btn_use_tailored = QPushButton("↩ Use Tailored")
        self.btn_export   = QPushButton("Export")

        for btn in (self.btn_new, self.btn_import, self.btn_use_tailored):
            btn.setProperty("panelButton", True)
            btn.setFixedHeight(30)

        self.btn_export.setFixedHeight(30)
        self.btn_export.setProperty("exportBtn", True)

        btn_bar_layout.addWidget(self.btn_new)
        btn_bar_layout.addWidget(self.btn_import)
        btn_bar_layout.addWidget(self.btn_use_tailored)
        btn_bar_layout.addWidget(self.btn_export)
        left_layout.addWidget(btn_bar)
        left_layout.addWidget(_divider())

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        form_widget = QWidget()
        form_widget.setObjectName("builderForm")
        form_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._form_layout = QVBoxLayout(form_widget)
        self._form_layout.setContentsMargins(16, 16, 16, 16)
        self._form_layout.setSpacing(16)

        self._build_personal_section()
        self._build_summary_section()
        self._build_experience_section()
        self._build_education_section()
        self._build_skills_section()
        self._build_projects_section()
        self._build_certifications_section()
        self._build_awards_section()

        self._form_layout.addStretch()
        scroll.setWidget(form_widget)
        left_layout.addWidget(scroll)

        # ── RIGHT: preview panel ──
        right_widget = QWidget()
        right_widget.setObjectName("builderRight")
        right_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        preview_header = QWidget()
        preview_header.setObjectName("builderPreviewHeader")
        ph_layout = QHBoxLayout(preview_header)
        ph_layout.setContentsMargins(16, 12, 16, 12)
        lbl_preview = QLabel("Live Preview")
        lbl_preview.setProperty("panelTitle", True)
        self.lbl_style_badge = QLabel("Style: Prestige")
        self.lbl_style_badge.setProperty("styleBadge", True)
        ph_layout.addWidget(lbl_preview)
        ph_layout.addStretch()
        ph_layout.addWidget(self.lbl_style_badge)
        right_layout.addWidget(preview_header)
        right_layout.addWidget(_divider())

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setObjectName("builderPreview")
        self.preview_text.setPlaceholderText(
            "Fill in the form on the left — your resume will appear here..."
        )
        right_layout.addWidget(self.preview_text)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([520, 560])
        root.addWidget(splitter)

        # Wire entry point buttons
        self.btn_new.clicked.connect(self._on_new)
        self.btn_import.clicked.connect(self._on_import)
        self.btn_use_tailored.clicked.connect(self._on_use_tailored)
        self.btn_export.clicked.connect(self._on_export)

    # ── Section builders ──────────────────────────────────────────────────────
    def _build_personal_section(self):
        grp = QGroupBox("Personal Information")
        grp.setObjectName("builderCard")
        layout = QFormLayout(grp)
        layout.setSpacing(8)

        self.inp_name     = QLineEdit(); self.inp_name.setPlaceholderText("Full Name")
        self.inp_title    = QLineEdit(); self.inp_title.setPlaceholderText("Professional Title")
        self.inp_email    = QLineEdit()
        self.inp_email.setPlaceholderText("email@example.com")
        self.inp_email.textEdited.connect(self._on_email_typed)

        # Email domain suggestion chips (hidden until @ is typed)
        self._email_chips_widget = QWidget()
        self._email_chips_widget.setObjectName("emailChips")
        self._email_chips_layout = QHBoxLayout(self._email_chips_widget)
        self._email_chips_layout.setContentsMargins(0, 2, 0, 0)
        self._email_chips_layout.setSpacing(4)
        self._email_chips_widget.setVisible(False)

        EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "hotmail.com"]
        for domain in EMAIL_DOMAINS:
            btn = QPushButton(f"@{domain.split('.')[0]}")
            btn.setProperty("emailChip", True)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda _, d=domain: self._apply_email_domain(d))
            self._email_chips_layout.addWidget(btn)
        self._email_chips_layout.addStretch()
        self.inp_phone    = QLineEdit()
        self.inp_phone.setPlaceholderText("(555) 555-5555")
        self.inp_phone.textEdited.connect(self._format_phone)
        self.inp_location = QLineEdit(); self.inp_location.setPlaceholderText("City, State")
        # LinkedIn prefix + handle only
        linkedin_row = QHBoxLayout()
        lbl_li_prefix = QLabel("linkedin.com/in/")
        lbl_li_prefix.setProperty("builderFieldLabel", True)
        lbl_li_prefix.setStyleSheet("font-family: monospace; padding-right: 2px;")
        self.inp_linkedin = QLineEdit()
        self.inp_linkedin.setPlaceholderText("yourhandle")
        self.inp_linkedin.setToolTip("Enter just your LinkedIn handle — the full URL is built automatically")
        linkedin_row.addWidget(lbl_li_prefix)
        linkedin_row.addWidget(self.inp_linkedin)
        self.inp_website  = QLineEdit(); self.inp_website.setPlaceholderText("yourwebsite.com (optional)")

        layout.addRow("Name:",     self.inp_name)
        layout.addRow("Title:",    self.inp_title)
        layout.addRow("Email:",    self.inp_email)
        layout.addRow("",          self._email_chips_widget)
        layout.addRow("Phone:",    self.inp_phone)
        layout.addRow("Location:", self.inp_location)
        li_container = QWidget()
        li_container.setLayout(linkedin_row)
        layout.addRow("LinkedIn:", li_container)
        layout.addRow("Website:",  self.inp_website)

        for w in (self.inp_name, self.inp_title, self.inp_email, self.inp_phone,
                  self.inp_location, self.inp_linkedin, self.inp_website):
            w.textChanged.connect(self._debounce.start)

        self._form_layout.addWidget(grp)

    def _build_summary_section(self):
        grp = QGroupBox("Professional Summary")
        grp.setObjectName("builderCard")
        layout = QVBoxLayout(grp)

        hdr = QHBoxLayout()
        hdr.addWidget(_field_label("Summary"))
        hdr.addStretch()
        self.btn_improve_summary = _ai_btn("Improve summary with AI")
        self.btn_improve_summary.clicked.connect(self._improve_summary)
        hdr.addWidget(self.btn_improve_summary)
        layout.addLayout(hdr)

        self.inp_summary = QTextEdit()
        self.inp_summary.setPlaceholderText(
            "Write 2-4 sentences highlighting your top skills and what you bring to this role..."
        )
        self.inp_summary.setFixedHeight(100)
        self.inp_summary.setObjectName("builderTextEdit")
        self.inp_summary.textChanged.connect(self._debounce.start)
        layout.addWidget(self.inp_summary)
        self._form_layout.addWidget(grp)

    def _build_experience_section(self):
        self._exp_group = QGroupBox("Work Experience")
        self._exp_group.setObjectName("builderCard")
        self._exp_layout = QVBoxLayout(self._exp_group)

        btn_add = QPushButton("+ Add Role")
        btn_add.setProperty("addSectionBtn", True)
        btn_add.clicked.connect(self._add_work_card)
        self._exp_layout.addWidget(btn_add)
        self._form_layout.addWidget(self._exp_group)

    def _add_work_card(self, entry: WorkEntry = None):
        card = _WorkCard(entry, self)
        card.changed.connect(self._debounce.start)
        card.removed.connect(self._remove_work_card)
        self._work_cards.append(card)
        # Insert before the Add button (last item)
        insert_pos = self._exp_layout.count() - 1
        self._exp_layout.insertWidget(insert_pos, card)
        self._debounce.start()

    def _remove_work_card(self, card: _WorkCard):
        self._work_cards.remove(card)
        self._exp_layout.removeWidget(card)
        card.deleteLater()
        self._debounce.start()

    def _build_education_section(self):
        grp = QGroupBox("Education")
        grp.setObjectName("builderCard")
        layout = QFormLayout(grp)
        layout.setSpacing(8)

        self.inp_degree  = QLineEdit(); self.inp_degree.setPlaceholderText("Degree & Concentration")
        self.inp_school  = QLineEdit(); self.inp_school.setPlaceholderText("School Name")
        self.inp_ed_loc  = QLineEdit(); self.inp_ed_loc.setPlaceholderText("City, State")

        # Graduation row: date field + "Currently Enrolled" toggle
        grad_row = QHBoxLayout()
        self.inp_ed_end  = QLineEdit(); self.inp_ed_end.setPlaceholderText("Graduation (e.g. May 2026)")
        self.chk_enrolled = QCheckBox("Currently Enrolled")
        self.chk_enrolled.toggled.connect(self._on_enrolled_toggled)
        grad_row.addWidget(self.inp_ed_end, 2)
        grad_row.addWidget(self.chk_enrolled)
        grad_container = QWidget()
        grad_container.setLayout(grad_row)

        self.inp_gpa     = QLineEdit(); self.inp_gpa.setPlaceholderText("GPA (optional)")
        self.inp_ed_note = QLineEdit(); self.inp_ed_note.setPlaceholderText("Honors, concentrations (optional)")

        layout.addRow("Degree:",   self.inp_degree)
        layout.addRow("School:",   self.inp_school)
        layout.addRow("Location:", self.inp_ed_loc)
        layout.addRow("Graduated:", grad_container)
        layout.addRow("GPA:",      self.inp_gpa)
        layout.addRow("Notes:",    self.inp_ed_note)

        for w in (self.inp_degree, self.inp_school, self.inp_ed_loc,
                  self.inp_ed_end, self.inp_gpa, self.inp_ed_note):
            w.textChanged.connect(self._debounce.start)

        self._form_layout.addWidget(grp)

    def _build_skills_section(self):
        self._skills_group = QGroupBox("Skills")
        self._skills_group.setObjectName("builderCard")
        self._skills_layout = QVBoxLayout(self._skills_group)

        btn_row = QHBoxLayout()
        btn_add_skill = QPushButton("+ Add Skill")
        btn_add_skill.setProperty("addSectionBtn", True)
        btn_add_skill.clicked.connect(lambda: self._add_skill_row())

        self.btn_suggest_skills = _ai_btn("Suggest skills based on your experience")
        self.btn_suggest_skills.setText("✨ Suggest Skills")
        self.btn_suggest_skills.clicked.connect(self._suggest_skills)

        btn_row.addWidget(btn_add_skill)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_suggest_skills)
        self._skills_layout.addLayout(btn_row)

        self._form_layout.addWidget(self._skills_group)

    def _add_skill_row(self, entry: SkillEntry = None):
        row = _SkillRow(entry, self)
        row.changed.connect(self._debounce.start)
        row.removed.connect(self._remove_skill_row)
        self._skill_rows.append(row)
        insert_pos = self._skills_layout.count() - 1
        self._skills_layout.insertWidget(insert_pos, row)
        self._debounce.start()

    def _remove_skill_row(self, row: _SkillRow):
        self._skill_rows.remove(row)
        self._skills_layout.removeWidget(row)
        row.deleteLater()
        self._debounce.start()

    def _build_projects_section(self):
        grp = QGroupBox("Projects")
        grp.setObjectName("builderCard")
        layout = QFormLayout(grp)
        layout.setSpacing(8)

        self.inp_proj_name  = QLineEdit(); self.inp_proj_name.setPlaceholderText("Project Name")
        self.inp_proj_tech  = QLineEdit(); self.inp_proj_tech.setPlaceholderText("React, Python, PostgreSQL...")
        self.inp_proj_date  = QLineEdit(); self.inp_proj_date.setPlaceholderText("Year or date range")
        self.inp_proj_url   = QLineEdit(); self.inp_proj_url.setPlaceholderText("GitHub or live URL (optional)")

        proj_desc_hdr = QHBoxLayout()
        proj_desc_hdr.addWidget(_field_label("Description"))
        proj_desc_hdr.addStretch()
        self.btn_improve_proj = _ai_btn("Improve project description with AI")
        self.btn_improve_proj.clicked.connect(self._improve_project)
        proj_desc_hdr.addWidget(self.btn_improve_proj)

        self.inp_proj_desc = QTextEdit()
        self.inp_proj_desc.setPlaceholderText("What did you build? What problem did it solve?")
        self.inp_proj_desc.setFixedHeight(80)
        self.inp_proj_desc.setObjectName("builderTextEdit")

        layout.addRow("Name:",         self.inp_proj_name)
        layout.addRow("Technologies:", self.inp_proj_tech)
        layout.addRow("Date:",         self.inp_proj_date)
        layout.addRow("URL:",          self.inp_proj_url)
        layout.addRow(proj_desc_hdr)
        layout.addRow(self.inp_proj_desc)

        for w in (self.inp_proj_name, self.inp_proj_tech, self.inp_proj_date, self.inp_proj_url):
            w.textChanged.connect(self._debounce.start)
        self.inp_proj_desc.textChanged.connect(self._debounce.start)

        self._form_layout.addWidget(grp)

    def _build_certifications_section(self):
        grp = QGroupBox("Certifications")
        grp.setObjectName("builderCard")
        layout = QFormLayout(grp)
        layout.setSpacing(8)

        self.inp_cert_name   = QLineEdit(); self.inp_cert_name.setPlaceholderText("Certification Name")
        self.inp_cert_issuer = QLineEdit(); self.inp_cert_issuer.setPlaceholderText("Issuing Organization")
        self.inp_cert_date   = QLineEdit(); self.inp_cert_date.setPlaceholderText("Date obtained")
        self.inp_cert_url    = QLineEdit(); self.inp_cert_url.setPlaceholderText("Verification URL (optional)")

        layout.addRow("Name:",   self.inp_cert_name)
        layout.addRow("Issuer:", self.inp_cert_issuer)
        layout.addRow("Date:",   self.inp_cert_date)
        layout.addRow("URL:",    self.inp_cert_url)

        for w in (self.inp_cert_name, self.inp_cert_issuer, self.inp_cert_date, self.inp_cert_url):
            w.textChanged.connect(self._debounce.start)

        self._form_layout.addWidget(grp)

    def _build_awards_section(self):
        grp = QGroupBox("Awards / Recognitions / Volunteer Work")
        grp.setObjectName("builderCard")
        layout = QVBoxLayout(grp)

        self.inp_awards = QTextEdit()
        self.inp_awards.setPlaceholderText("One item per line:\nNational Society of Collegiate Scholars (NSCS) — Member\nDean's List, Fall 2024")
        self.inp_awards.setFixedHeight(90)
        self.inp_awards.setObjectName("builderTextEdit")
        self.inp_awards.textChanged.connect(self._debounce.start)
        layout.addWidget(self.inp_awards)
        self._form_layout.addWidget(grp)

    # ── Education toggle ─────────────────────────────────────────────────────
    def _on_enrolled_toggled(self, checked: bool):
        """Make grad date read-only with forbidden cursor when enrolled."""
        from PyQt6.QtGui import QCursor
        from PyQt6.QtCore import Qt as _Qt
        self.inp_ed_end.setReadOnly(checked)
        if checked:
            self.inp_ed_end.setText("")
            self.inp_ed_end.setPlaceholderText("In Progress")
            self.inp_ed_end.setCursor(QCursor(_Qt.CursorShape.ForbiddenCursor))
            self.inp_ed_end.setProperty("fieldLocked", True)
        else:
            self.inp_ed_end.setPlaceholderText("Graduation (e.g. May 2026)")
            self.inp_ed_end.setCursor(QCursor(_Qt.CursorShape.IBeamCursor))
            self.inp_ed_end.setProperty("fieldLocked", False)
        self.inp_ed_end.style().unpolish(self.inp_ed_end)
        self.inp_ed_end.style().polish(self.inp_ed_end)
        self._debounce.start()

    # ── Entry point handlers ──────────────────────────────────────────────────
    def _on_new(self):
        reply = QMessageBox.question(
            self, "New Resume",
            "Clear all fields and start a blank resume?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._clear_form()

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Resume", "",
            "Resume Files (*.pdf *.docx)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".pdf"):
                from core.extractor.pdf_parser import extract_pdf
                text = extract_pdf(path)
            else:
                from core.extractor.docx_parser import extract_docx
                text = extract_docx(path)
            self._prefill_from_text(text)
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))

    def _on_use_tailored(self):
        try:
            win = self.window()
            if hasattr(win, "tailored_text") and win.tailored_text:
                self._prefill_from_text(win.tailored_text)
            elif hasattr(win, "resume_text") and win.resume_text:
                self._prefill_from_text(win.resume_text)
            else:
                QMessageBox.information(
                    self, "No Resume",
                    "Tailor a resume first, or load one on the Tailor tab."
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _prefill_from_text(self, text: str):
        """Parse plain text into form fields using simple heuristics."""
        from core.processor.cleaner import clean_resume_text
        text = clean_resume_text(text)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return

        # Name = first line
        self.inp_name.setText(lines[0] if lines else "")

        # Title = second line if not a section heading
        if len(lines) > 1 and not lines[1].isupper():
            # Strip location from title line
            title_parts = lines[1].split(",")
            self.inp_title.setText(title_parts[0].strip())
            if len(title_parts) > 1:
                self.inp_location.setText(title_parts[-1].strip())

        # Email
        import re
        email_match = re.search(r"[\w._%+-]+@[\w.-]+\.\w+", text)
        if email_match:
            self.inp_email.setText(email_match.group())

        # Phone
        phone_match = re.search(r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}", text)
        if phone_match:
            self.inp_phone.setText(phone_match.group())

        # LinkedIn
        linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.I)
        if linkedin_match:
            self.inp_linkedin.setText(linkedin_match.group())

        # Summary — text between SUMMARY heading and next heading
        summary_match = re.search(
            r"SUMMARY\s*\n(.*?)(?=\n[A-Z]{3,}|\Z)", text, re.DOTALL | re.I
        )
        if summary_match:
            self.inp_summary.setPlainText(summary_match.group(1).strip())

        # Awards
        awards_match = re.search(
            r"(?:AWARDS?|RECOGNITIONS?|VOLUNTEER).*?\n(.*?)(?=\n[A-Z]{3,}|\Z)",
            text, re.DOTALL | re.I
        )
        if awards_match:
            self.inp_awards.setPlainText(awards_match.group(1).strip())

        self._debounce.start()

    def _on_export(self):
        text = self._build_resume_data().to_plain_text()
        if not text.strip():
            QMessageBox.warning(self, "Empty", "Fill in at least your name before exporting.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Resume", "My_Resume.docx", "Word Document (*.docx)"
        )
        if not path:
            return

        try:
            style = "prestige"
            win = self.window()
            if hasattr(win, "ui") and hasattr(win.ui, "tabSettings"):
                style = win.ui.tabSettings.get_selected_style()
            from core.exporter.resume_style_engine import ResumeStyleEngine
            ResumeStyleEngine().export(text, style=style, output_path=path)
            QMessageBox.information(self, "Exported", f"Resume saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    # ── AI assist handlers ────────────────────────────────────────────────────
    def _improve_summary(self):
        text = self.inp_summary.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Empty", "Write a summary first.")
            return
        self.btn_improve_summary.setText("✨ Improving...")
        self.btn_improve_summary.setEnabled(False)
        context = f"{self.inp_title.text()} with experience at {', '.join([c.inp_company.text() for c in self._work_cards[:2]])}"
        self._worker = self._ai.improve_summary(text, context)
        self._worker.finished.connect(self._on_summary_improved)
        self._worker.error.connect(lambda _: self._reset_summary_btn())
        self._worker.start()

    def _on_summary_improved(self, text: str):
        self.inp_summary.setPlainText(text)
        self._reset_summary_btn()

    def _reset_summary_btn(self):
        self.btn_improve_summary.setText("✨ Improve")
        self.btn_improve_summary.setEnabled(True)

    def _improve_project(self):
        desc = self.inp_proj_desc.toPlainText().strip()
        if not desc:
            QMessageBox.information(self, "Empty", "Add a project description first.")
            return
        self.btn_improve_proj.setText("✨ Improving...")
        self.btn_improve_proj.setEnabled(False)
        self._worker = self._ai.improve_project(
            self.inp_proj_name.text(), desc, self.inp_proj_tech.text()
        )
        self._worker.finished.connect(self._on_project_improved)
        self._worker.error.connect(lambda _: self._reset_proj_btn())
        self._worker.start()

    def _on_project_improved(self, text: str):
        self.inp_proj_desc.setPlainText(text)
        self._reset_proj_btn()

    def _reset_proj_btn(self):
        self.btn_improve_proj.setText("✨ Improve")
        self.btn_improve_proj.setEnabled(True)

    def _suggest_skills(self):
        context = f"{self.inp_title.text()}. Experience: {', '.join([c.inp_company.text() for c in self._work_cards])}"
        existing = [r.get_entry().name for r in self._skill_rows]
        self.btn_suggest_skills.setText("✨ Suggesting...")
        self.btn_suggest_skills.setEnabled(False)
        self._worker = self._ai.suggest_skills(context, existing)
        self._worker.finished.connect(self._on_skills_suggested)
        self._worker.error.connect(lambda _: self._reset_skills_btn())
        self._worker.start()

    def _on_skills_suggested(self, text: str):
        skills = [s.strip() for s in text.split(",") if s.strip()]
        for skill in skills:
            self._add_skill_row(SkillEntry(name=skill, proficiency="Proficient"))
        self._reset_skills_btn()

    def _reset_skills_btn(self):
        self.btn_suggest_skills.setText("✨ Suggest Skills")
        self.btn_suggest_skills.setEnabled(True)

    # ── Data collection ───────────────────────────────────────────────────────
    def _build_resume_data(self) -> ResumeData:
        d = ResumeData()
        d.personal.name     = self.inp_name.text().strip()
        d.personal.title    = self.inp_title.text().strip()
        d.personal.email    = self.inp_email.text().strip()
        d.personal.phone    = self.inp_phone.text().strip()
        d.personal.location = self.inp_location.text().strip()
        handle = self.inp_linkedin.text().strip().lstrip("/")
        d.personal.linkedin = f"linkedin.com/in/{handle}" if handle else ""

        d.personal.website  = self.inp_website.text().strip()
        d.summary           = self.inp_summary.toPlainText().strip()
        d.experience        = [c.get_entry() for c in self._work_cards]
        ed_end = "In Progress" if self.chk_enrolled.isChecked() else self.inp_ed_end.text().strip()
        d.education         = [EducationEntry(
            degree    = self.inp_degree.text().strip(),
            school    = self.inp_school.text().strip(),
            location  = self.inp_ed_loc.text().strip(),
            end_date  = ed_end,
            gpa       = self.inp_gpa.text().strip(),
            notes     = self.inp_ed_note.text().strip(),
        )]
        d.skills            = [r.get_entry() for r in self._skill_rows]
        if self.inp_proj_name.text().strip():
            d.projects = [ProjectEntry(
                name         = self.inp_proj_name.text().strip(),
                description  = self.inp_proj_desc.toPlainText().strip(),
                technologies = self.inp_proj_tech.text().strip(),
                url          = self.inp_proj_url.text().strip(),
                date         = self.inp_proj_date.text().strip(),
            )]
        if self.inp_cert_name.text().strip():
            d.certifications = [CertificationEntry(
                name   = self.inp_cert_name.text().strip(),
                issuer = self.inp_cert_issuer.text().strip(),
                date   = self.inp_cert_date.text().strip(),
                url    = self.inp_cert_url.text().strip(),
            )]
        d.awards = [
            l.strip() for l in self.inp_awards.toPlainText().splitlines()
            if l.strip()
        ]
        return d

    # ── Preview ───────────────────────────────────────────────────────────────
    def _refresh_preview(self):
        data  = self._build_resume_data()
        text  = data.to_plain_text()
        if not text.strip():
            self.preview_text.setPlainText("")
            return
        # Update style badge
        try:
            win = self.window()
            if hasattr(win, "ui") and hasattr(win.ui, "tabSettings"):
                style_key = win.ui.tabSettings.get_selected_style()
                from app.components.style_picker_widget import STYLE_DEFS
                label = next((s["name"] for s in STYLE_DEFS if s["key"] == style_key), style_key)
                self.lbl_style_badge.setText(f"Style: {label}")
        except Exception:
            pass
        self.preview_text.setPlainText(text)

    # ── Clear form ────────────────────────────────────────────────────────────
    # ── Input formatting helpers ─────────────────────────────────────────────
    def _format_phone(self, text: str):
        """Auto-format phone number as (XXX) XXX-XXXX while typing."""
        import re
        digits = re.sub(r"\D", "", text)[:10]
        if len(digits) <= 3:
            formatted = digits
        elif len(digits) <= 6:
            formatted = f"({digits[:3]}) {digits[3:]}"
        else:
            formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        # Only update if actually different to avoid cursor jump
        if self.inp_phone.text() != formatted:
            self.inp_phone.blockSignals(True)
            self.inp_phone.setText(formatted)
            self.inp_phone.blockSignals(False)
            self.inp_phone.setCursorPosition(len(formatted))

    def _on_email_typed(self, text: str):
        """Show domain suggestion chips after @ is typed."""
        if "@" in text and not text.endswith("@"):
            # Already has domain — hide chips
            self._email_chips_widget.setVisible(False)
        elif "@" in text and text.endswith("@"):
            # Just typed @ — show chips
            self._email_chips_widget.setVisible(True)
        elif "@" not in text:
            self._email_chips_widget.setVisible(False)

    def _apply_email_domain(self, domain: str):
        """Append the selected domain to the email field."""
        current = self.inp_email.text()
        if "@" in current:
            base = current.split("@")[0]
        else:
            base = current
        self.inp_email.setText(f"{base}@{domain}")
        self._email_chips_widget.setVisible(False)
        self._debounce.start()

    def _clear_form(self):
        for w in (self.inp_name, self.inp_title, self.inp_email, self.inp_phone,
                  self.inp_location, self.inp_linkedin, self.inp_website,
                  self.inp_degree, self.inp_school, self.inp_ed_loc,
                  self.inp_ed_end, self.inp_gpa, self.inp_ed_note,
                  self.inp_proj_name, self.inp_proj_tech, self.inp_proj_date,
                  self.inp_proj_url, self.inp_cert_name, self.inp_cert_issuer,
                  self.inp_cert_date, self.inp_cert_url):
            w.clear()
        for te in (self.inp_summary, self.inp_proj_desc, self.inp_awards):
            te.clear()
        self.chk_enrolled.setChecked(False)
        for card in list(self._work_cards):
            self._remove_work_card(card)
        for row in list(self._skill_rows):
            self._remove_skill_row(row)
        self.preview_text.clear()

    # ── Public: populate from outside (e.g. when tab is switched to) ──────────
    def load_tailored(self, text: str):
        """Called by window_main when user navigates to Builder with tailored text."""
        if text:
            self._prefill_from_text(text)