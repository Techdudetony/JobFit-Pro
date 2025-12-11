"""
Utility helpers for extracting structured fields from job descriptions.
"""

import re


def extract_company_role(job_text: str):
    """
    Attempts to extract (company, role) from a raw job description string.
    Returns ("Unknown", "Unknown") if not enough information is available.

    Handles formats such as:
        - "Company — Role"
        - "Role at Company"
        - "Company: X"
        - "Title: X"
        - "Hiring Company: X"
        - LinkedIn headers:
              "Job Title\nCompany Name · Location"
        - Pasted descriptions with first-line titles
    """

    if not job_text or not job_text.strip():
        return "Unknown", "Unknown"

    text = job_text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # ---------------------------------------------------------
    # 1. Check first line for common "Company — Role" pattern
    # ---------------------------------------------------------
    first = lines[0]

    dash_pattern = r"^(?P<company>.+?)\s*[-–—]\s*(?P<role>.+)$"
    m = re.match(dash_pattern, first)
    if m:
        return m.group("company").strip(), m.group("role").strip()

    # ---------------------------------------------------------
    # 2. Check for "Role at Company"
    # ---------------------------------------------------------
    at_pattern = r"^(?P<role>.+?)\s+at\s+(?P<company>.+)$"
    m = re.match(at_pattern, first, re.IGNORECASE)
    if m:
        return m.group("company").strip(), m.group("role").strip()

    # ---------------------------------------------------------
    # 3. LinkedIn Style:
    #    Line 1 = Title
    #    Line 2 = Company
    # ---------------------------------------------------------
    if len(lines) >= 2:
        # Example:
        # Software Engineer
        # Google · Mountain View, CA
        role_candidate = lines[0]
        company_candidate = re.split(r"·|\||-", lines[1])[0].strip()

        if role_candidate and company_candidate:
            return (company_candidate, role_candidate)

    # ---------------------------------------------------------
    # 4. Pattern: "Title: X"
    # ---------------------------------------------------------
    m = re.search(r"(Title|Role)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if m:
        role = m.group(2).strip()

        # Maybe Company appears elsewhere
        m2 = re.search(
            r"(Company|Employer|Hiring Company)\s*[:\-]\s*(.+)",
            text,
            re.IGNORECASE,
        )
        company = m2.group(2).strip() if m2 else "Unknown"

        return company, role

    # ---------------------------------------------------------
    # 5. Pattern: "Company: X"
    # ---------------------------------------------------------
    m = re.search(
        r"(Company|Employer|Hiring Company)\s*[:\-]\s*(.+)", text, re.IGNORECASE
    )
    if m:
        company = m.group(2).strip()

        # Role may be first non-empty line
        role = lines[0] if lines else "Unknown"
        return company, role

    # ---------------------------------------------------------
    # 6. Fallback:
    #    Assume First Line = Role
    #    Assume Second Line = Company
    # ---------------------------------------------------------
    role = lines[0] if lines else "Unknown"
    company = lines[1] if len(lines) > 1 else "Unknown"

    return company, role
