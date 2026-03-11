"""
Job Description Fetcher & Cleaner
----------------------------------------------------

Fetches job descriptions from URLs, removes noise, and extracts clean,
ATS-ready text for LLM processing.
"""

import requests
import re
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_job_description(url: str) -> str:
    """
    Download a job page and extract meaningful description text.
    Returns an empty string on failure.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("[JOB PARSER ERROR]", e)
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove elements that contain no job content
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "aside",
            "form",
            "img",
        ]
    ):
        tag.extract()

    # Remove common junk sections by class name
    for cls in ["cookie", "footer", "header", "sidebar", "nav"]:
        for tag in soup.find_all(class_=lambda x: x and cls in x.lower()):
            tag.decompose()

    # Extract visible text
    raw_text = soup.get_text(separator="\n")

    # Clean + format text
    cleaned = _clean_job_text(raw_text)
    return cleaned.strip()


def _clean_job_text(text: str) -> str:
    """
    Cleans extracted job text:
    - Removes navigation boilerplate
    - Fixes bullet points
    - Normalizes spacing
    - Removes legal disclaimers & junk
    """
    # Replace HTML-style bullets with '-'
    text = re.sub(r"[•◦▪◦♦■]", "- ", text)

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove very short lines (likely navigation elements)
    lines = text.splitlines()
    useful_lines = [line.strip() for line in lines if len(line.strip()) > 3]

    # Remove common boilerplate patterns
    filtered = []
    for line in useful_lines:
        if any(
            bad in line.lower()
            for bad in [
                "accept cookies",
                "privacy policy",
                "cookie policy",
                "terms of service",
                "login",
                "sign in",
                "subscribe",
                "apply now",
                "related jobs",
                "follow us",
            ]
        ):
            continue
        filtered.append(line)

    return "\n".join(filtered).strip()