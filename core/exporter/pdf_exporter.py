"""
PDF Exporter
--------------------------------

Converts tailored resume text into a PDF by:
1. Building a temporary DOCX using the shared DOCX exporter
2. Converting that DOCX into a PDF using docx2pdf

This function isolates PDF export logic and ensures consistent formatting export types.
"""

import os, tempfile

from core.exporter.docx_builder import export_to_docx
from docx2pdf import convert


def export_to_pdf(text: str, save_path: str) -> str | None:
    """
    Export resume text to a PDF file.
    Returns the final PDF path on success, or None on error.
    """

    # Normalize output extension
    base, ext = os.path.splitext(save_path)
    if ext.lower() != ".pdf":
        save_path = base + ".pdf"

    # Ensure directory exists
    directory = os.path.dirname(save_path) or "."
    os.makedirs(directory, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_docx = os.path.join(tmpdir, "temp_resume.docx")

            # Create DOCX via the shared builder
            export_to_docx(text, temp_docx)

            # Convert DOCX to PDF
            convert(temp_docx, save_path)

        return save_path
    except Exception as e:
        print("[PDF EXPORT ERROR]", e)
        return None
