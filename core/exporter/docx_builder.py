'''
Exports tailored resume text into DOCX
'''
from docx import Document

def export_to_docx(text: str, output_path: str):
    doc = Document()
    
    for line in text.split("\n"):
        doc.add_paragraph(line)
        
    doc.save(output_path)