"""
Keyword extraction and overlap scoring.
Lightweight ATS-friendly keyword analyzer.
"""

import re
from collections import Counter

# Basic stopword list
STOPWORDS = {
    "the",
    "and",
    "to",
    "in",
    "for",
    "of",
    "a",
    "an",
    "on",
    "with",
    "is",
    "as",
    "by",
    "at",
    "from",
    "this",
    "that",
    "it",
    "be",
    "are",
}

WORD_PATTERN = r"[A-Za-z0-9\-]+"  # Supports Numbers + hyphens + acronyms


def extract_keywords(text: str):
    """
    Extracts normalized keywords from text, excluding stopwords.
    Returns a Counter for frequency analysis.
    """
    words = re.findall(WORD_PATTERN, text.lower())
    filtered = [word for word in words if word not in STOPWORDS and len(word) > 2]
    return Counter(filtered)


def keyword_overlap(job_text: str, resume_text: str):
    """
    Returns keyword overlap + scoring metadata:
    - overlapping keywords with job frequencies
    - missing job keywords
    - match rate as a percentage
    """
    job_kw = extract_keywords(job_text)
    resume_kw = extract_keywords(resume_text)

    overlap = {word: job_kw[word] for word in job_kw if word in resume_kw}
    missing = {word: job_kw[word] for word in job_kw if word not in resume_kw}

    match_rate = (len(overlap) / max(len(job_kw), 1)) * 100  # Avoid division by 0

    return {
        "overlap": overlap,
        "missing": missing,
        "match_rate": round(match_rate, 2),
        "job_keyword_count": len(job_kw),
        "resume_keyword_count": len(resume_kw),
    }
