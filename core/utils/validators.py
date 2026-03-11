"""
Validation utilities for JobFit Pro
---------------------------------------

This module contains reusable, UI-agnostic validation functions for resume
files, job URLs, text content, and tailoring settings.
"""

import os, re
from urllib.parse import urlparse


# --------------------------------------------------------------------
# FILE VALIDATION
# --------------------------------------------------------------------
def is_supported_resume_file(path: str) -> bool:
    """Return TRUE if the file extension is a supported resume type."""
    if not path:
        return False

    ext = os.path.splitext(path)[1].lower()
    return ext in {".pdf", ".docx"}


def file_exists(path: str) -> bool:
    """Check whether the provided file path exists."""
    return os.path.isfile(path)


# --------------------------------------------------------------------
# TEXT VALIDATION
# --------------------------------------------------------------------
def has_meaningful_text(text: str, threshold: int = 30) -> bool:
    """
    Returns TRUE if the provided text appears meaningful.
    Threshold prevents empty HTML-scraped content or blank resumes.
    """
    if not text:
        return False

    return len(text.strip()) >= threshold


# --------------------------------------------------------------------
# URL VALIDATION
# --------------------------------------------------------------------
def is_valid_url(url: str) -> bool:
    """Simple syntactic URL validation."""
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except Exception:
        return False


# --------------------------------------------------------------------
# SETTINGS VALIDATION
# --------------------------------------------------------------------
def validate_tailor_settings(settings: dict) -> bool:
    """
    Check that tailoring settings from SettingsPanel are valid.
    This keeps the controller clean and testable.
    """
    if not isinstance(settings, dict):
        return False

    allowed_keys = {"limit_pages", "limit_one_page"}

    return all(key in allowed_keys for key in settings.keys())
