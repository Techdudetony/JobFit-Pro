"""
PDF Resume Extraction Utility
---------------------------------------------

Uses pdfplumber for structured text extraction and includes basic
cleanup and fallback hndling for better resume processing.
"""

import pdfplumber, re


def extract_pdf(path: str) -> str:
    """
    Extract text from a PDF resume.
    Handles common PDF artifacts and gracefully skips unreadable pages.
    """
    pages_text = []

    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                # Extract text (returns None for scanned-only pages)
                content = page.extract_text()

                if not content:
                    # Page is likely scanned or empty
                    continue

                cleaned = _clean_pdf_text(content)
                pages_text.append(cleaned)
    except Exception as e:
        print("[PDF PARSER ERROR]", e)
        return ""

    combined = "\n\n".join(pages_text).strip()
    return combined


def _clean_pdf_text(page_text: str) -> str:
    """
    Removes common PDF extraction noise: headers, footers, excessive
    whitespace, broken lines, and odd unicode characters.
    """
    # Remove zero-width/invisible unicode characters
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E]", "", page_text)

    # Remove repeated header/footer patterns
    # Examples: "Page 1 of 3", "1 / 3", "Resume – John Doe"
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.I)
    text = re.sub(r"^\s*\d+\s*/\s*\d+\s*$", "", text, flags=re.M)

    # Normalize spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Normalize newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
