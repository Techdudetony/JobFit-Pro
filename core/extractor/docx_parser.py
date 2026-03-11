'''
Extract text from DOCX resume files.
Handles both paragraph text and table cell content,
since many resumes use tables for layout.
'''
from docx import Document

def extract_docx(path: str) -> str:
    doc = Document(path)
    parts = []

    # Extract paragraph text
    for p in doc.paragraphs:
        if p.text.strip():
            parts.append(p.text)

    # Extract table cell text (many resumes use tables for layout)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)

    return "\n".join(parts).strip()