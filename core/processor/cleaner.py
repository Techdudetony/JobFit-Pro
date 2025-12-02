'''
Utility formatting tools used before/after processing.
'''
import re

def clean_resume_text(text: str) -> str:
    # Normalize spacing and remove weird artifacts.
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\t", " ")
    return text.strip()