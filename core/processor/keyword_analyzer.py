# core/processor/keyword_analyzer.py
"""
OpenAI-Powered Keyword Analyzer — JobFit Pro
---------------------------------------------

Replaces heuristic keyword matching with a single GPT call that:
  1. Identifies which job keywords were successfully matched in the tailored resume
  2. Suggests keywords the user MIGHT have but weren't included
     (conservative — never fabricates skills)
  3. Flags if any skills/experiences in the resume look potentially fabricated
  4. Returns an overall ATS match score (0-100)

Returns a structured dict that ATSPanel consumes directly.
"""

import json
import re
from textwrap import dedent

from services.openai_client import OpenAIClient


ANALYSIS_PROMPT = dedent(
    """
You are an expert ATS (Applicant Tracking System) analyst and resume coach.

You will be given:
1. A JOB DESCRIPTION
2. A TAILORED RESUME

Your task is to analyze the resume against the job description and return a JSON object
with the following structure. Return ONLY valid JSON — no markdown, no explanation.

{{
  "ats_score": <integer 0-100, overall keyword/relevance match>,
  "matched_keywords": [
    {{"keyword": "string", "context": "brief note on where/how it appears in resume"}}
  ],
  "suggested_additions": [
    {{
      "keyword": "string",
      "reason": "brief reason why this is relevant and plausible for this candidate",
      "confidence": "high|medium|low"
    }}
  ],
  "fabrication_warnings": [
    {{
      "item": "string (the skill/experience that looks suspicious)",
      "reason": "why it looks potentially fabricated or inconsistent"
    }}
  ],
  "section_scores": {{
    "Summary": <integer 0-100 or null if section absent>,
    "Experience": <integer 0-100 or null if section absent>,
    "Skills": <integer 0-100 or null if section absent>,
    "Education": <integer 0-100 or null if section absent>,
    "Projects": <integer 0-100 or null if section absent>
  }},
  "summary": "2-3 sentence overall assessment"
}}

Rules:
- matched_keywords: only include keywords that genuinely appear AND are relevant to the job
- suggested_additions: ONLY suggest skills/tools that a person with this background plausibly has
  but simply didn't mention. Never invent skills. Max 10 suggestions.
- fabrication_warnings: flag anything that appears in the resume but contradicts or
  seems inconsistent with the candidate's actual background. Empty list if nothing suspicious.
- section_scores: score each section on how well it addresses the job requirements.
  Use null (not 0) for sections that don't exist in the resume.
- ats_score: holistic score, not just keyword count — consider relevance, specificity, alignment.

JOB DESCRIPTION:
{job_text}

TAILORED RESUME:
{resume_text}
"""
)


def analyze_keywords(job_text: str, resume_text: str) -> dict:
    """
    Run OpenAI keyword analysis. Returns a structured dict.
    On failure returns a safe fallback dict with error info.
    """
    client = OpenAIClient()

    prompt = ANALYSIS_PROMPT.format(
        job_text=job_text[:3000],
        resume_text=resume_text[:3000],
    )

    try:
        raw = client.generate(prompt, temperature=0.1, max_tokens=1500)
        return _parse_response(raw)
    except Exception as e:
        print(f"[KEYWORD ANALYZER] Error: {e}")
        return _fallback(str(e))


def _parse_response(raw: str) -> dict:
    """Extract and parse the JSON block from the model response."""
    # Strip markdown code fences if present
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract just the JSON object
        match = re.search(r"\{[\s\S]+\}", raw)
        if match:
            try:
                data = json.loads(match.group())
            except Exception:
                return _fallback("Could not parse model response as JSON.")
        else:
            return _fallback("No JSON found in model response.")

    # Normalize / fill missing keys safely
    return {
        "ats_score": int(data.get("ats_score", 0)),
        "matched_keywords": data.get("matched_keywords", []),
        "suggested_additions": data.get("suggested_additions", []),
        "fabrication_warnings": data.get("fabrication_warnings", []),
        "section_scores": data.get("section_scores", {}),
        "summary": data.get("summary", ""),
        "error": None,
    }


def _fallback(error_msg: str) -> dict:
    return {
        "ats_score": 0,
        "matched_keywords": [],
        "suggested_additions": [],
        "fabrication_warnings": [],
        "section_scores": {},
        "summary": "",
        "error": error_msg,
    }
