"""
AI Resume Tailoring Engine
------------------------------------

Uses OpenAI to rewrite resumes according to job descriptions, with
optional length-control rules. This module contains no UI logic and
is safe for unit testing.
"""

from textwrap import dedent
from services.openai_client import OpenAIClient
from core.processor.cleaner import clean_resume_text

DEFAULT_TAILOR_PROMPT = dedent(
    """
    You are an expert resume editor and hiring strategist specializing in ATS optimization.
    Your goal is to rewrite the user's resume so that it aligns directly with the job description.
    
    Follow these rules STRICTLY:
    
    ---------------------------------------
    ### 1. ALIGNMENT TO JOB DESCRIPTION
    ---------------------------------------
    - Identify the top required skills, tools, and responsibilities from the job description.
    - Emphasize the user's matching experience by rewriting bullet points to highlight these skills.
    - Add missing keywords ONLY if they legitimately fit the user's background.
    - Strengthen technical and measurable achievements whenever possible.
    
    ---------------------------------------
    ### 2. FORMAT & STRUCTURE
    ---------------------------------------
    - Keep the original resume structure (sections, order, flow).
    - Maintain bullet points where they existed.
    - Use concise, impactful, professional language.
    - Ensure ATS-friendly output: no tables, columns, icons, images, or unusual characters.
    
    ---------------------------------------
    ### 3. STYLE & TONE
    ---------------------------------------
    - Professional, confident, and results-oriented.
    - Avoid fluff, fillers, and corporate jargon.
    
    ---------------------------------------
    ### 4. LENGTH CONTROL
    ---------------------------------------
    Default target: approx. **1-2 pages** (450-650 words) unless overridden.
    
    ---------------------------------------
    ### 5. OUTPUT
    ---------------------------------------
    Return ONLY the rewritten resume.
    No explanations, notes, or markdown formatting.
    
    ---------------------------------------
    
    ### USER_RESUME:
    {resume_text}
    
    ### JOB DESCRIPTION:
    {job_text}
"""
)


class ResumeTailor:
    def __init__(self, temperature: float = 0.3):
        """Lower temperature yields more consistent, deterministic resumes."""
        self.client = OpenAIClient()
        self.temperature = temperature

    # ----------------------------------------------------------------------
    # Internal Helper: Build extra rules dynamically
    # ----------------------------------------------------------------------
    def _build_length_rules(self, limit_pages: bool, limit_one: bool) -> str:
        extra = ""

        if limit_pages and not limit_one:
            extra += dedent(
                """
                -----------------------------------------------
                ### LENGTH ENFORCEMENT (1/2 PAGES)
                -----------------------------------------------
                - MUST fit within 1-2 pages.
                - Target: ~450-650 words.
                - Remove redundant and weak bullet points.
                - Merge overlapping content.
            """
            )

        if limit_one:
            extra += dedent(
                """
                -----------------------------------------------
                ### ONE-PAGE LENGTH ENFORCEMENT (STRICT)
                -----------------------------------------------
                - MUST fit a single page.
                - Prioritize recent, high-impact roles.
                - Remove older or irrelevant roles.
                - Tighten all bullet points.
            """
            )

        return extra

    # ----------------------------------------------------------------------
    # Public API: Generate tailored resume
    # ----------------------------------------------------------------------
    def generate(
        self,
        resume_text: str,
        job_text: str,
        limit_pages: bool = False,
        limit_one: bool = False,
        limit_one_page=None,
    ) -> str:
        # Allow limit_one_page as an alias
        if limit_one_page is not None:
            limit_one = limit_one_page

        resume_text = clean_resume_text(resume_text)
        extra_rules = self._build_length_rules(limit_pages, limit_one)

        prompt = (
            DEFAULT_TAILOR_PROMPT.format(resume_text=resume_text, job_text=job_text)
            + extra_rules
        )

        # Safe API call
        try:
            return self.client.generate(
                prompt,
                temperature=self.temperature,
                max_tokens=1200,  # Safe upperbound for rewrite
            )
        except Exception as e:
            print("[TAILOR ENGINE ERROR]", e)
            return "Error generating tailored resume. Please try again."
