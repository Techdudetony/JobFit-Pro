"""
Text cleaning utilities for resume preprocessing.

Removes common PDF/DOCX artifacts, normalizes whitespace, and
standardizes bullet formatting for better LLM processing.
"""

import re


def clean_resume_text(text: str) -> str:
    if not text:
        return ""

    # --------------------------------------------
    # Normalize bullets & special characters
    # --------------------------------------------
    bullet_variants = [r"•", r"●", r"▪", r"–", r"—", r"- ", r"– ", r"— "]
    for bullet in bullet_variants:
        text = text.replace(bullet, "- ")

    # Replace curly quotes/dashes
    text = (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
    )

    # Remove weird invisible unicode characters
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E]", "", text)

    # -----------------------------------------
    # Normalize whitespace
    # -----------------------------------------
    text = text.replace("\t", " ")
    text = re.sub(r"[ ]{2,}", " ", text)  # collapse multiple spaces
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse >=3 newlines to 2

    # Trim leading/trailing space on all lines
    text = "\n".join(line.strip() for line in text.splitlines())

    # Remove blank lines at the start/end
    return text.strip()
