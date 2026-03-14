"""
ResumeBuilderAI
---------------
Focused AI improvement calls for individual Resume Builder sections.
Each method takes the raw user input for a section and returns an
improved version — no full resume rewrite needed.
"""

from textwrap import dedent
from PyQt6.QtCore import QThread, pyqtSignal
from services.openai_client import OpenAIClient


IMPROVE_SUMMARY_PROMPT = dedent("""
You are an expert resume writer. Improve the professional summary below.
Make it concise (2-4 sentences), specific, results-oriented, and free of
personal pronouns. No fluff. No buzzwords.

Context about the candidate:
{context}

Current summary:
{text}

Return ONLY the improved summary text. No explanation.
""")

IMPROVE_BULLETS_PROMPT = dedent("""
You are an expert resume writer. Improve the bullet points below for the
role of {role} at {company}.

Rules:
- Start each bullet with a strong action verb (past tense)
- Quantify results wherever possible or use scale language
- Remove weak openers: "Responsible for", "Helped", "Assisted"
- Keep each bullet to 1-2 lines
- No personal pronouns

Current bullets:
{bullets}

Return ONLY the improved bullet points, one per line, each starting with "- ".
No explanation.
""")

IMPROVE_PROJECT_PROMPT = dedent("""
You are an expert resume writer. Improve this project description for a
software/tech resume.

Project: {name}
Technologies: {technologies}

Current description:
{description}

Make it concrete, impact-focused, and 2-3 bullet points max.
Return ONLY the improved description, bullets starting with "- ".
No explanation.
""")

SUGGEST_SKILLS_PROMPT = dedent("""
Based on this work experience and background, suggest 8-12 additional
relevant technical or professional skills this person likely has but
hasn't listed yet. Only suggest skills that are plausible given their
actual experience — never fabricate.

Background:
{context}

Already listed skills:
{existing}

Return ONLY a comma-separated list of skill names. No explanation.
""")


class _BaseImproveWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, prompt: str):
        super().__init__()
        self._prompt = prompt

    def run(self):
        try:
            client = OpenAIClient()
            result = client.generate(self._prompt, temperature=0.3, max_tokens=600)
            self.finished.emit(result.strip())
        except Exception as e:
            self.error.emit(str(e))


class ResumeBuilderAI:
    """
    Provides worker factories for each AI-assist action.
    Callers keep a reference to the worker to prevent GC.
    """

    def improve_summary(self, summary: str, context: str = "") -> _BaseImproveWorker:
        prompt = IMPROVE_SUMMARY_PROMPT.format(text=summary, context=context or "N/A")
        return _BaseImproveWorker(prompt)

    def improve_bullets(self, bullets: str,
                        role: str = "", company: str = "") -> _BaseImproveWorker:
        prompt = IMPROVE_BULLETS_PROMPT.format(
            bullets=bullets, role=role or "this role", company=company or "this company"
        )
        return _BaseImproveWorker(prompt)

    def improve_project(self, name: str, description: str,
                        technologies: str = "") -> _BaseImproveWorker:
        prompt = IMPROVE_PROJECT_PROMPT.format(
            name=name, description=description, technologies=technologies or "various"
        )
        return _BaseImproveWorker(prompt)

    def suggest_skills(self, context: str, existing: list[str]) -> _BaseImproveWorker:
        prompt = SUGGEST_SKILLS_PROMPT.format(
            context=context,
            existing=", ".join(existing) if existing else "none"
        )
        return _BaseImproveWorker(prompt)