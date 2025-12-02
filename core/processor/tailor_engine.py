"""
LLM-powered resume tailoring engine.
"""

from services.openai_client import OpenAIClient
from core.processor.cleaner import clean_resume_text
from textwrap import dedent

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
- Target approx. **1–2 pages**, ~450–650 words.
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

    def generate(self, resume_text: str, job_text: str) -> str:
        resume_text = clean_resume_text(resume_text)

        prompt = TAILOR_ENGINE_PROMPT.format(resume_text=resume_text, job_text=job_text)

        return self.client.generate(prompt)
