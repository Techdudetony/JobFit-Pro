'''
Extract text from PDF resume files. 
'''
import pdfplumber

def extract_pdf(path: str) -> str:
    text = ""
    
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            content = page.extract_text() or ""
            text += content + "\n"
            
    return text.strip()