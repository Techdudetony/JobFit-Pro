"""
ContextQuestionEngine
----------------------

Analyzes the user's resume + job description and generates 4-5
personalized clarifying questions as structured JSON.

Each question has one of four types:
  - "yes_no"          → two-option binary choice (rendered as radio buttons)
  - "single_choice"   → pick one from a list (rendered as radio buttons)
  - "multiple_choice" → pick one or more (rendered as checkboxes)
  - "text"            → free-text response (rendered as QTextEdit)

JSON schema returned by OpenAI:
[
  {
    "type": "yes_no" | "single_choice" | "multiple_choice" | "text",
    "key": "unique_snake_case_key",
    "question": "The question text shown to the user",
    "options": ["Option A", "Option B", ...],   // required for all except text
    "placeholder": "Hint text for text inputs"  // only for text type
  },
  ...
]
"""

import json
from textwrap import dedent
from PyQt6.QtCore import QThread, pyqtSignal
from services.openai_client import OpenAIClient


QUESTION_GEN_PROMPT = dedent(
    """
    You are an expert resume coach analyzing a candidate's resume and a job description.
    Your task is to generate 4-5 personalized clarifying questions that will help
    tailor the resume more accurately and honestly.

    The questions should feel personal and specific — reference actual details from
    the resume (job titles, specific metrics, skills, gaps, dates) and the job description.

    Cover these categories across your questions (not all need a dedicated question,
    but try to touch on most):
    - Gaps or weak spots in the resume relative to the job
    - Skills or projects from the background worth highlighting for this specific role
    - Years of experience clarification (especially if the resume shows a pivot or gap)
    - Career goals or transition intent
    - Achievements that exist but aren't quantified or are underrepresented

    Question type rules:
    - Use "yes_no" for simple binary decisions (2 options only)
    - Use "single_choice" when one answer best fits (3-5 options, mutually exclusive)
    - Use "multiple_choice" when several answers might apply (3-5 options, can select many)
    - Use "text" for open-ended answers where the candidate needs to elaborate
    - Mix the types — do not make all questions the same type
    - Aim for 2-3 choice-based questions and 1-2 text questions

    IMPORTANT RULES:
    - Reference specifics from the resume: real job titles, real metrics, real skills
    - Reference specifics from the job description: exact role requirements, tech stack
    - Options in choice questions must be concrete and meaningful — not generic
    - Never ask for information already clearly present in the resume
    - Keep question text concise (1-2 sentences max)

    Return ONLY a valid JSON array. No explanation, no markdown, no code fences.
    The array must contain between 4 and 5 question objects.

    Each object must have:
      "type": one of "yes_no", "single_choice", "multiple_choice", "text"
      "key": a unique snake_case identifier (e.g. "career_goal", "highlight_skill")
      "question": the question text string
      "options": array of strings (required for yes_no, single_choice, multiple_choice)
      "placeholder": hint string (required for text type only)

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_text}
    """
)

# Fallback questions used if OpenAI call fails
FALLBACK_QUESTIONS = [
    {
        "type": "single_choice",
        "key": "goal",
        "question": "What is your primary goal for this application?",
        "options": [
            "Career transition into this field",
            "Advancement in my current career path",
            "Returning to this type of role",
            "Exploring opportunities",
        ],
    },
    {
        "type": "multiple_choice",
        "key": "emphasize",
        "question": "Which areas of your background should we emphasize most?",
        "options": [
            "Technical skills and tools",
            "Leadership and management experience",
            "Measurable achievements and metrics",
            "Education and certifications",
        ],
    },
    {
        "type": "yes_no",
        "key": "side_projects",
        "question": "Do you have relevant personal or side projects not listed on your resume?",
        "options": ["Yes — I'll describe them below", "No"],
    },
    {
        "type": "text",
        "key": "additional",
        "question": "Is there anything else about your background or goals you want the tailoring to reflect?",
        "placeholder": "e.g. I recently completed a relevant certification, I'm relocating, I prefer remote work...",
    },
]


class ContextQuestionWorker(QThread):
    """
    Background worker that calls OpenAI to generate personalized questions.
    Emits a list of question dicts on success, or falls back to static questions on error.
    """

    finished = pyqtSignal(list)   # emits list of question dicts
    error    = pyqtSignal(str)

    def __init__(self, resume_text: str, job_text: str):
        super().__init__()
        self.resume_text = resume_text
        self.job_text    = job_text

    def run(self):
        try:
            client = OpenAIClient()
            prompt = QUESTION_GEN_PROMPT.format(
                resume_text=self.resume_text[:3000],  # cap to avoid token waste
                job_text=self.job_text[:2000],
            )
            raw = client.generate(prompt, temperature=0.5, max_tokens=800)

            # Strip markdown fences if GPT wraps in ```json ... ```
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                cleaned = cleaned.rsplit("```", 1)[0]

            questions = json.loads(cleaned)

            # Validate basic structure
            if not isinstance(questions, list) or len(questions) < 2:
                raise ValueError("Invalid question list returned")

            self.finished.emit(questions)

        except Exception as e:
            print(f"[CONTEXT ENGINE] Falling back to static questions: {e}")
            self.finished.emit(FALLBACK_QUESTIONS)