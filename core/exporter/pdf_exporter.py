import os
import tempfile
from core.exporter.docx_builder import export_to_docx
from docx2pdf import convert


def export_to_pdf(text: str, save_path: str):
    """
    Export tailored resume text to PDF by:
    1) Creating a temporary DOCX via your existing exporter
    2) Converting that DOCX to PDF with docx2pdf
    """

    # Normalize extension to .pdf
    base, ext = os.path.splitext(save_path)
    if ext.lower() != ".pdf":
        save_path = base + ".pdf"

    # Ensure directory exists
    directory = os.path.dirname(save_path) or "."
    os.makedirs(directory, exist_ok=True)

    # Use a temp directory for the intermediate DOCX
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_docx = os.path.join(tmpdir, "temp_resume.docx")

        # Use your existing DOCX builder so formatting stays consistent
        export_to_docx(text, temp_docx)

        # Convert DOCX → PDF
        convert(temp_docx, save_path)
