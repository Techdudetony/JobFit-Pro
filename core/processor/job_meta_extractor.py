# core/processor/job_meta_extractor.py
"""
OpenAI-powered Company & Role extractor.
Runs as a lightweight background worker after tailoring completes.
Returns {"company": str, "role": str} from raw job description text.
"""

import json
import re
from textwrap import dedent
from PyQt6.QtCore import QThread, pyqtSignal


EXTRACT_PROMPT = dedent(
    """
You are parsing a job posting. Extract ONLY the company name and job title/role.

Return ONLY this JSON, nothing else:
{{"company": "<company name>", "role": "<job title>"}}

Rules:
- company: the hiring organization's name (e.g. "CarMax", "Google", "Towne Bank")
- role: the specific job title (e.g. "Strategy Analyst", "Software Engineer II")
- If you cannot determine one, use "Unknown"
- No extra text, no markdown, just the JSON object

JOB POSTING:
{job_text}
"""
)


def extract_job_meta(job_text: str) -> dict:
    """Synchronous call — run inside a QThread worker."""
    from services.openai_client import OpenAIClient

    client = OpenAIClient()

    prompt = EXTRACT_PROMPT.format(job_text=job_text[:2000])
    try:
        raw = client.generate(prompt, temperature=0.0, max_tokens=60)
        raw = raw.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return {
            "company": str(data.get("company", "Unknown")).strip(),
            "role": str(data.get("role", "Unknown")).strip(),
        }
    except Exception as e:
        print(f"[JOB META] Extraction failed: {e}")
        return {"company": "Unknown", "role": "Unknown"}


class JobMetaWorker(QThread):
    """Extracts company + role in background, then saves history entry."""

    finished = pyqtSignal(dict)  # emits {"company": ..., "role": ...}

    def __init__(self, job_text: str):
        super().__init__()
        self.job_text = job_text

    def run(self):
        result = extract_job_meta(self.job_text)
        self.finished.emit(result)
