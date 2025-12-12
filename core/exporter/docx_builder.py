"""
DOCX Resume Exporter
---------------------------------

Formats LLM-generated resume text into clean, ATS-friendly DOCX output
with normalized spacing, heading detection, and bullet lists.
"""

import re

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.style import WD_STYLE_TYPE


def export_to_docx(text: str, output_path: str):
    doc = Document()

    # -------------------------------------------
    # Page Setup
    # -------------------------------------------
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    # -------------------------------------------
    # Base "Normal" Style
    # -------------------------------------------
    normal_style = doc.styles["Normal"]
    norm_font = normal_style.font
    norm_font.name = "Calibri"
    norm_font.size = Pt(11)

    norm_para = normal_style.paragraph_format
    norm_para.space_before = Pt(0)
    norm_para.space_after = Pt(2)
    norm_para.line_spacing = 1.0

    # -------------------------------------------
    # Heading Style
    # -------------------------------------------
    styles = doc.styles
    if "Resume Heading" in styles:
        heading_style = styles["Resume Heading"]
    else:
        heading_style = styles.add_style("Resume Heading", WD_STYLE_TYPE.PARAGRAPH)
        h_font = heading_style.font
        h_font.name = "Calibri"
        h_font.size = Pt(11)
        h_font.bold = True
        h_font.all_caps = True

        h_para = heading_style.paragraph_format
        h_para.space_before = Pt(6)
        h_para.space_after = Pt(2)
        h_para.line_spacing = 1.0

    # -------------------------------------------
    # Bullet Style
    # -------------------------------------------
    bullet_style_name = "List Bullet"
    # FIXED: Use try/except instead of .get()
    try:
        bullet_style = styles[bullet_style_name]
    except KeyError:
        bullet_style = normal_style

    # -------------------------------------------
    # Helper Functions
    # -------------------------------------------
    COMMON_SECTION_NAMES = {
        "experience",
        "work experience",
        "professional experience",
        "summary",
        "profile",
        "education",
        "skills",
        "projects",
        "certifications",
        "achievements",
        "leadership",
    }

    def is_section_heading(line: str) -> bool:
        """Identify headings using heuristics"""
        cleaned = line.strip()

        if not cleaned or len(cleaned) > 60:
            return False

        # Exact matches or close matches with common headings
        if cleaned.lower() in COMMON_SECTION_NAMES:
            return True

        # If 60%+ uppercase letters ... treat as a heading
        letters = [char for char in cleaned if char.isalpha()]
        if letters:
            if sum(char.isupper() for char in letters) / len(letters) > 0.6:
                return True

        # Title Case words like "Work Experience"
        if cleaned.istitle():
            return True

        return False

    def is_bullet(line: str) -> bool:
        stripped = line.lstrip()
        return stripped.startswith(("-", "•", "*", "–", "—"))

    def clean_bullet_text(line: str) -> str:
        """Normalize bullet prefixes to standard '- '."""
        stripped = line.lstrip()
        for prefix in ("- ", "• ", "* ", "– ", "— ", "-", "•", "*", "–", "—"):
            if stripped.startswith(prefix):
                return stripped[len(prefix) :].strip()
        return stripped

    # -------------------------------------------
    # Main Line Processing
    # -------------------------------------------
    lines = text.splitlines()
    last_was_blank = False
    last_was_bullet = False

    for raw_line in lines:
        line = raw_line.rstrip()

        # Blank lines
        if not line.strip():
            if not last_was_blank:
                doc.add_paragraph("")
            last_was_blank = True
            last_was_bullet = False
            continue

        last_was_blank = False
        stripped = line.strip()

        # Headings
        if is_section_heading(stripped):
            para = doc.add_paragraph(stripped)
            para.style = heading_style
            last_was_bullet = False
            continue

        # Bullet
        if is_bullet(stripped):
            bullet_text = clean_bullet_text(stripped)
            # FIXED: Check if style exists before using
            try:
                para = doc.add_paragraph(bullet_text, style=bullet_style_name)
            except KeyError:
                para = doc.add_paragraph(bullet_text)
                # Manually format as bullet if style doesn't exist
                para.style = normal_style
            last_was_bullet = True
            continue

        # Continuation of bullet?
        if last_was_bullet:
            try:
                para = doc.add_paragraph(stripped, style=bullet_style_name)
            except KeyError:
                para = doc.add_paragraph(stripped)
                para.style = normal_style
            continue

        # Normal text
        para = doc.add_paragraph(stripped)
        para.style = normal_style
        last_was_bullet = False

    # Save DOCX
    doc.save(output_path)
