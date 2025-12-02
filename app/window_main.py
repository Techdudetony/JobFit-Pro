'''
UI logic controller for the application
'''
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from core.extractor.pdf_parser import extract_pdf
from core.extractor.docx_parser import extract_docx
from core.extractor.job_parser import fetch_job_description
from core.exporter.docx_builder import export_to_docx
from core.processor.tailor_engine import ResumeTailor

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        from app.ui.main_window import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Event Bindings
        self.ui.btnLoadResume.clicked.connect(self.load_resume)
        self.ui.btnFetchJob.clicked.connect(self.fetch_job)
        self.ui.btnTailor.clicked.connect(self.tailor_resume)
        self.ui.btnExport.clicked.connect(self.export_output)
        
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""
        
    # --------------------------------------------------------------------------
    
    def load_resume(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Resume", "", "PDF Files (*.pdf);;Word Files (*.docx)"
        )
        
        if not fname:
            return
        
        if fname.endswith(".pdf"):
            self.resume_text = extract_pdf(fname)
        else:
            self.resume_text = extract_docx(fname)
            
        self.ui.resumePreview.setPlainText(self.resume_text)
        
    # --------------------------------------------------------------------------

    def fetch_job(self):
        url = self.ui.inputJobURL.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a job URL.")
            return
        
        self.job_text = fetch_job_description(url)
        
        if not self.job_text:
            QMessageBox.warning(self, "Error", "Could not fetch job description.")
            return
        
        self.ui.jobPreview.setPlainText(self.job_text)
    
    # --------------------------------------------------------------------------

    def tailor_resume(self):
        if not self.resume_text or not self.job_text:
            QMessageBox.warning(self, "Error", "Load both resume and job text.")
            return
        
        self.tailored_text = self.tailor.generate(self.resume_text, self.job_text)
        self.ui.outputPreview.setPlainText(self.tailored_text)
        
    # --------------------------------------------------------------------------
    
    def export_output(self):
        if not self.tailored_text:
            QMessageBox.warning(self, "Error", "Nothing to export.")
            return
        
        fname, _ = QFileDialog.getSaveFileName(
            self, "Save Tailored Resume", "Tailored_Resume.docx", "Word Document (*.docx)"
        )
        
        if not fname:
            return
        
        export_to_docx(self.tailored_text, fname)
        QMessageBox.information(self, "Success", "Resume exported successfully!")