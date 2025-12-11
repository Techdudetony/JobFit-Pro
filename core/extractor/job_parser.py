"""
Job Description Fetcher & Cleaner
----------------------------------------------------

Fetches job descriptions from URLs, removes noise, and extracts clean,
ATS-ready text for LLM processing.
"""

import requests, re

from bs4 import BeautifulSoup


def fetch_job_description(url: str) -> str:
    """
    Download a job page and extract meaningful description text.
    Returns an empty string on failure.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("[JOB PARSER ERROR]", e)
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove Irrelevant tags that clutter output
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

    # Remove common junk sections
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
    - Removes bavigation boilerplate
    - Fixes bullet points
    - Normalizes spacing
    - Removes legal disclaimers & junk
    """
    # Replace HTML-style bullets with '-'
    text = re.sub(r"[•●▪◦♦■]", "- ", text)

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove very short lines that are likely navigation elements
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

    cleaned = "\n".join(filtered)

    return cleaned.strip()
