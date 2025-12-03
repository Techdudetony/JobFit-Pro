"""
LLM-powered resume tailoring engine.
"""

from textwrap import dedent
from services.openai_client import OpenAIClient
from core.processor.cleaner import clean_resume_text


TAILOR_ENGINE_PROMPT = dedent(
    """
    You are an expert resume editor and hiring strategist specializing in ATS optimization.

    Your goal is to rewrite the user's resume so that it aligns directly with the job description.

    Follow these rules STRICTLY:

    -----------------------------------
    ### 1. ALIGNMENT TO JOB DESCRIPTION
    -----------------------------------
    - Identify the top required skills, tools, and responsibilities from the job description.
    - Emphasize the user’s matching experience by rewriting bullet points to highlight these skills.
    - Add missing keywords ONLY if they legitimately fit the user's background.
    - Strengthen technical and measurable achievements whenever possible.

    -----------------------------------
    ### 2. FORMAT & STRUCTURE
    -----------------------------------
    - Keep the original resume structure (sections, order, general flow).
    - Maintain bullet points wherever they originally existed.
    - Use concise, impactful, professional language.
    - Ensure the resume is ATS-friendly:
      - No tables
      - No columns
      - No graphics
      - No emojis or icons
      - No unusual characters

    -----------------------------------
    ### 3. STYLE & TONE
    -----------------------------------
    - Professional
    - Confident
    - Results-oriented
    - Avoid excessive fluff, filler, or corporate jargon.

    -----------------------------------
    ### 4. LENGTH CONTROL
    -----------------------------------
    - Target approx. **1–2 pages**, ~450–650 words by default.
    - Remove weak, outdated, or irrelevant details if necessary.
    - Merge redundant bullet points.

    -----------------------------------
    ### 5. OUTPUT
    -----------------------------------
    Return ONLY the rewritten resume text.
    Do NOT include explanations, headers, commentary, or markdown formatting.

    -----------------------------------

    ### USER RESUME:
    {resume_text}

    ### JOB DESCRIPTION:
    {job_text}
    """
)


class ResumeTailor:
    def __init__(self):
        self.client = OpenAIClient()

    def generate(
        self,
        resume_text: str,
        job_text: str,
        limit_pages: bool = False,
        limit_one: bool = False,
    ) -> str:
        resume_text = clean_resume_text(resume_text)

        extra_rules = ""

        # 1–2 pages mode
        if limit_pages and not limit_one:
            extra_rules += dedent(
                """
                ---------------------------------
                ### LENGTH ENFORCEMENT (1–2 PAGES)
                ---------------------------------
                - The rewritten resume MUST comfortably fit within 1–2 pages.
                - Target length: roughly **450–650 words**.
                - Remove redundant, outdated, or weak bullet points.
                - Merge repetitive content and tighten overly long sections.
                """
            )

        # One-page mode (stricter)
        if limit_one:
            extra_rules += dedent(
                """
                -----------------------------------------
                ### ONE-PAGE LENGTH ENFORCEMENT (STRICT)
                -----------------------------------------
                - The rewritten resume MUST fit on **a single page**.
                - Aggressively prioritize the most recent and relevant experience.
                - Remove older or low-impact roles unless they contain critical skills.
                - Keep bullet points very concise and impact-focused.
                - Avoid long paragraphs; favor short, punchy statements.
                """
            )

        prompt = (
            TAILOR_ENGINE_PROMPT.format(
                resume_text=resume_text,
                job_text=job_text,
            )
            + extra_rules
        )

        return self.client.generate(prompt)
