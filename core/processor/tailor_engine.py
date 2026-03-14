"""
AI Resume Tailoring Engine
------------------------------------

Uses OpenAI to rewrite resumes according to job descriptions, with
optional length-control rules. This module contains no UI logic and
is safe for unit testing.

Prompt informed by:
- Harvard FAS Career Services resume guide
- Indeed: 10 Resume Writing Tips (Genevieve Northup, Dec 2025)
- LinkedIn HR post: Oluwatoyin Adeyemo (responsibilities vs. achievements)
- LinkedIn recruiter post: Ali Gauley (10-second scan rule)
"""

from textwrap import dedent
from services.openai_client import OpenAIClient
from core.processor.cleaner import clean_resume_text


DEFAULT_TAILOR_PROMPT = dedent(
    """
    You are an expert resume editor, ATS specialist, and hiring strategist.
    You know exactly what recruiters look for in the first 10 seconds of scanning a resume,
    and what makes applicant tracking systems accept or reject a candidate.

    Your goal is to rewrite the user's resume so it aligns strongly with the job description,
    passes ATS screening, and impresses a human recruiter reading quickly.

    Follow ALL of these rules STRICTLY:

    -----------------------------------------------
    ### 1. ALIGNMENT TO JOB DESCRIPTION
    -----------------------------------------------
    - Carefully read the job description and identify:
        a) Required and preferred skills
        b) Tools, technologies, or methodologies mentioned
        c) Key responsibilities and outcomes the employer expects
        d) Exact language and terminology the employer uses
    - Rewrite bullet points to mirror that language naturally where it fits the user's background.
    - Embed keywords from the "Requirements" and "Qualifications" sections throughout --
      especially in the Summary and most recent experience.
    - ONLY add keywords and skills that legitimately fit the user's real background. Never fabricate.

    -----------------------------------------------
    ### 2. HONESTY & ACCURATE REPRESENTATION (CRITICAL)
    -----------------------------------------------
    Your job is to present the candidate in the BEST HONEST LIGHT -- not to invent experience
    they do not have. A recruiter who interviews the candidate will quickly discover any
    exaggerations, which destroys credibility.

    Rules:
    - Do NOT overstate years of experience. If the resume shows 2 years of development
      experience, do not write "5+ years" simply because the job asks for it.
    - Do NOT claim proficiency in tools or languages not present in the resume
      (e.g., do not add Golang, Electron, or Google Cloud if they are absent).
    - If there is a clear skill gap between the resume and the job description, do NOT
      paper over it with vague language. Instead:
        a) Maximize the transferable skills that DO apply
        b) Frame adjacent experience honestly (e.g., "Python and data analysis background
           with growing full-stack experience" rather than "5+ years full-stack")
        c) Let the actual work history speak -- strong honest bullets beat inflated summaries
    - The summary must accurately reflect the candidate's real experience level and background.
      It should position them as a strong candidate for what they genuinely bring, not for
      what the job requires them to have.

    -----------------------------------------------
    ### 3. ACHIEVEMENTS OVER RESPONSIBILITIES (CRITICAL)
    -----------------------------------------------
    Recruiters skip resumes that list what someone was "responsible for."
    They hire candidates who show what they actually accomplished.

    - Every bullet point should follow: WHAT you did + HOW you did it + THE RESULT
    - Lead every bullet with a strong, specific ACTION VERB.
      Use past tense for prior roles, present tense for current role.
      Strong verbs: Achieved, Spearheaded, Reduced, Launched, Optimized, Delivered,
      Negotiated, Automated, Consolidated, Designed, Implemented, Mentored, Generated,
      Streamlined, Exceeded, Overhauled, Directed, Secured, Transformed, Built.
    - NEVER start a bullet with:
        "Responsible for", "Helped with", "Assisted in", "Worked on", "Duties included"
      These are weak and passive. Rewrite them into direct, active statements.
    - NEVER use personal pronouns (I, we, my, our).
    - Quantify results wherever possible. Numbers make achievements concrete and scannable.
      If the original resume has numbers, preserve and emphasize them.
      If not, use language that implies scale or impact:
      "across 3 departments", "for a team of 12", "reducing processing time significantly".
    - Keep each bullet to 1-2 lines. Recruiters do not read long paragraphs -- they scan.
    - Do not repeat the same action verb more than twice in the entire resume.
    - Remove filler phrases: "various", "multiple tasks", "etc.", "a number of".

    -----------------------------------------------
    ### 4. PROFESSIONAL SUMMARY
    -----------------------------------------------
    - If the resume has a summary or profile section, rewrite it to:
        a) Open with the candidate's honest professional identity or current level
        b) Reflect the top 2-3 skills most relevant to this specific job description
           that the candidate ACTUALLY has
        c) Be 2-4 sentences -- concise enough to read in under 5 seconds
        d) Be written without personal pronouns -- confident and specific
    - Example of a strong, honest summary for a candidate transitioning into full-stack:
        "Computer Science graduate and QA professional with hands-on experience in
        JavaScript, TypeScript, React, and Python. Track record of data-driven process
        improvement and audit program design, with growing full-stack development skills
        and a strong foundation in software quality."
    - If no summary exists, do NOT add one unless the role strongly warrants it.

    -----------------------------------------------
    ### 5. SKILLS SECTION
    -----------------------------------------------
    - If a skills section exists, update it to surface the most relevant skills
      from the job description that the user legitimately possesses.
    - Separate hard skills (tools, technologies, certifications) from soft skills
      where both are present.
    - Remove generic filler: "Microsoft Office", "team player", "fast learner",
      "good communicator" -- unless explicitly required by the job description.
    - Do NOT add tools or technologies absent from the original resume.

    -----------------------------------------------
    ### 6. CONTENT PRIORITIZATION
    -----------------------------------------------
    - Keep the most recent and relevant experience prominent.
    - Include only the 3-5 most impactful bullet points per role -- quality over quantity.
    - Trim or remove roles older than 10 years unless they contain directly relevant skills.
    - Remove certifications, projects, or achievements with no relevance to this role.
    - Do NOT include: personal hobbies, references, headshots, age, or gender.

    -----------------------------------------------
    ### 7. FORMAT & ATS COMPLIANCE
    -----------------------------------------------
    - Preserve the original resume structure (section order, headings).
    - Maintain all bullet points where they originally existed.
    - Use clean, scannable formatting:
        - No tables, columns, text boxes, graphics, icons, or emojis
        - No unusual unicode characters or symbols
        - Standard section headings only (Experience, Education, Skills, Summary)
        - Consistent date formatting throughout (e.g., Jan 2021 - Mar 2023)
    - The resume must be readable in a top-to-bottom scan in under 10 seconds.
    - Break up any paragraph text into bullets wherever possible.

    -----------------------------------------------
    ### 8. LANGUAGE & TONE
    -----------------------------------------------
    - Specific rather than general ("Reduced churn by 18%" not "Improved retention")
    - Active rather than passive ("Led the migration" not "The migration was led by")
    - Written to express, not impress -- clear over complex
    - Consistent verb tense within each role section
    - Avoid buzzwords: "synergy", "guru", "ninja", "rockstar", "passionate about",
      "dynamic", "detail-oriented", "go-getter", "thought leader"

    -----------------------------------------------
    ### 9. LENGTH
    -----------------------------------------------
    - Default target: approximately 1-2 pages (450-650 words).
    - Prioritize depth on the most recent 2-3 roles.
    - Merge redundant bullets. Cut weak or irrelevant ones entirely.

    -----------------------------------------------
    ### 10. OUTPUT
    -----------------------------------------------
    Return ONLY the rewritten resume text.
    Do NOT include explanations, notes, commentary, or markdown formatting (no **, ##, ---).
    Preserve section headings in plain text (e.g., EXPERIENCE, EDUCATION, SKILLS).

    -----------------------------------------------

    ### USER RESUME:
    {resume_text}

    ### JOB DESCRIPTION:
    {job_text}
    """
)

# Optional context block appended when the user provides clarification answers
CONTEXT_BLOCK = dedent(
    """
    -----------------------------------------------
    ### ADDITIONAL CONTEXT FROM THE CANDIDATE
    -----------------------------------------------
    The candidate has provided the following additional context to guide the tailoring.
    Use this to make the resume more accurate and better targeted:

    {context}
    -----------------------------------------------
    """
)


class ResumeTailor:
    def __init__(self, temperature: float = 0.3):
        """Lower temperature yields more consistent, deterministic resumes."""
        self.client = OpenAIClient()
        self.temperature = temperature

    # ----------------------------------------------------------------------
    # Internal Helper: Build extra length rules dynamically
    # ----------------------------------------------------------------------
    def _build_length_rules(self, limit_pages: bool, limit_one: bool) -> str:
        extra = ""

        if limit_pages and not limit_one:
            extra += dedent(
                """
                -----------------------------------------------
                ### LENGTH ENFORCEMENT (1-2 PAGES)
                -----------------------------------------------
                - The rewritten resume MUST comfortably fit within 1-2 pages.
                - Target length: roughly 450-650 words.
                - Remove redundant, outdated, or weak bullet points.
                - Merge repetitive content and tighten overly long sections.
                """
            )

        if limit_one:
            extra += dedent(
                """
                -----------------------------------------------
                ### ONE-PAGE LENGTH ENFORCEMENT (STRICT)
                -----------------------------------------------
                - The rewritten resume MUST fit on a single page.
                - Aggressively prioritize the most recent and most relevant experience.
                - Limit each role to 2-3 tightly written bullet points.
                - Remove older or low-impact roles entirely unless they hold critical skills.
                - Keep the summary to 2 sentences maximum.
                - Every word must earn its place.
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
        context: str = "",
    ) -> str:
        # Support limit_one_page as an alias
        if limit_one_page is not None:
            limit_one = limit_one_page

        resume_text = clean_resume_text(resume_text)
        extra_rules = self._build_length_rules(limit_pages, limit_one)

        # Append optional candidate context block
        context_block = ""
        if context and context.strip():
            context_block = CONTEXT_BLOCK.format(context=context.strip())

        prompt = (
            DEFAULT_TAILOR_PROMPT.format(resume_text=resume_text, job_text=job_text)
            + extra_rules
            + context_block
        )

        # Safe API call
        try:
            return self.client.generate(
                prompt,
                temperature=self.temperature,
                max_tokens=1200,  # Safe upper bound for rewrite
            )
        except Exception as e:
            print("[TAILOR ENGINE ERROR]", e)
            return "Error generating tailored resume. Please try again."