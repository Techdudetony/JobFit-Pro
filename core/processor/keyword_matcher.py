'''
Extracts keywords from the job description and compares against the resume.
'''
import re
from collections import Counter

def extract_keywords(text: str):
    words = re.findall(r"[A-Za-z]+", text.lower())
    return Counter(words)

def keyword_overlap(job_text: str, resume_text: str):
    job_kw = extract_keywords(job_text)
    res_kw = extract_keywords(resume_text)
    
    overlap = {word: job_kw[word] for word in job_kw if word in res_kw}
    return overlap