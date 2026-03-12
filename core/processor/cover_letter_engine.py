# core/processor/cover_letter_engine.py
"""
AI Cover Letter Generator — JobFit Pro
---------------------------------------

Generates a tailored cover letter from resume text + job description.
Supports tone, length, and optional highlight instructions.
"""

from textwrap import dedent
from PyQt6.QtCore import QThread, pyqtSignal


TONE_INSTRUCTIONS = {
    "Professional": "formal, polished, and results-focused. Suitable for corporate or finance roles.",
    "Friendly": "warm, approachable, and conversational while remaining professional.",
    "Confident": "assertive, direct, and achievement-driven. Lead with impact.",
    "Creative": "engaging, distinctive, and memorable. Show personality while staying relevant.",
}

LENGTH_TARGETS = {
    "Short": ("~200 words", "3 short paragraphs"),
    "Standard": ("~350 words", "4 paragraphs"),
    "Detailed": ("~500 words", "5 paragraphs"),
}

COVER_LETTER_PROMPT = dedent(
    """
You are an expert career coach and professional writer specializing in cover letters.

Write a compelling, ATS-friendly cover letter based on the resume and job description below.

### TONE
{tone_instruction}

### LENGTH
Target {word_target} across {para_target}. Do not pad. Do not cut important content.

### STRUCTURE
1. Opening paragraph: Hook + role you're applying for + why this company specifically
2. Body paragraph(s): 2-3 of your strongest, most relevant achievements from the resume that match the job
3. Skills bridge: Connect your background directly to the job's key requirements
4. Closing: Clear call to action, enthusiasm, professional sign-off

### RULES
{highlight_instruction}
- Extract the applicant's name from the resume if present; sign off with it
- Address to "Hiring Team" unless a hiring manager name appears in the job description
- Do NOT use "I am writing to express my interest" or similar clichés
- Do NOT fabricate experience not present in the resume
- Do NOT use bullet points — flowing paragraphs only
- Do NOT include a date, address block, or subject line
- Prioritize keywords from the job description naturally woven into sentences

### RESUME
{resume_text}

### JOB DESCRIPTION
{job_text}

Return ONLY the cover letter text. No explanations, no markdown, no extra commentary.
"""
)


def generate_cover_letter(
    resume_text: str,
    job_text: str,
    tone: str = "Professional",
    length: str = "Standard",
    highlight: str = "",
) -> str:
    from services.openai_client import OpenAIClient

    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["Professional"])
    word_target, para_target = LENGTH_TARGETS.get(length, LENGTH_TARGETS["Standard"])

    highlight_instruction = (
        f"\n### MANDATORY HIGHLIGHTS — YOU MUST INCLUDE THESE\n"
        f"The user has specifically requested these points be prominently featured.\n"
        f"Do NOT bury them. Each item below must appear clearly and explicitly — not paraphrased away or mentioned in passing:\n"
        f"{highlight.strip()}\n"
        f"Dedicate at least one sentence per item directly to it. Treat this as non-negotiable."
        if highlight.strip()
        else ""
    )

    prompt = COVER_LETTER_PROMPT.format(
        tone_instruction=tone_instruction,
        word_target=word_target,
        para_target=para_target,
        highlight_instruction=highlight_instruction,
        resume_text=resume_text[:3000],
        job_text=job_text[:2000],
    )

    client = OpenAIClient()
    try:
        result = client.generate(prompt, temperature=0.6, max_tokens=900)
        return result.strip() if result else ""
    except Exception as e:
        print(f"[COVER LETTER ENGINE] {e}")
        return ""


class CoverLetterWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, resume_text, job_text, tone, length, highlight):
        super().__init__()
        self.resume_text = resume_text
        self.job_text = job_text
        self.tone = tone
        self.length = length
        self.highlight = highlight

    def run(self):
        try:
            result = generate_cover_letter(
                self.resume_text, self.job_text, self.tone, self.length, self.highlight
            )
            if result:
                self.finished.emit(result)
            else:
                self.error.emit(
                    "No output returned. Check your OpenAI API key and try again."
                )
        except Exception as e:
            self.error.emit(str(e))
