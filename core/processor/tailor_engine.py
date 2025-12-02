'''
LLM-powered resume tailoring engine.
'''
from services.openai_client import OpenAIClient
from core.processor.cleaner import clean_resume_text

class ResumeTailor:
    def __init__(self):
        self.client = OpenAIClient()
    
    def generate(self, resume_text: str, job_text: str) -> str:
        resume_text = clean_resume_text(resume_text)
        
        prompt = f"""
        You are an expert resume optimizer.
        Rewrite the resume to strongly match the job description.
        
        Guidelines:
        - Keep it ATS-friendly (no tables, no images).
        - Reword bullet points to align with job duties. 
        - Highlight relevant skills.
        - DO NOT invent experience.
        - Keep resume professional, concise, and structered.
        
        JOB DESCRIPTION:
        {job_text}
        
        ORIGINAL RESUME:
        {resume_text}
        
        RETURN ONLY the updated resume text.
        """
        
        return self.client.generate(prompt)