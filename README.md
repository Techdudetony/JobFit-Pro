# **JobFit Pro**

_A smart, AI-powered resume tailoring tool for Windows._

JobFit Pro is a modern desktop application designed to help job seekers quickly tailor their resumes to specific job descriptions. Built with **Python**, **PyQt6**, and **OpenAI**, the app extracts your resume, analyzes job postings, and generates a professionally aligned, ATS-friendly tailored version.

This tool is ideal for students, professionals, and job hunters who want to streamline their application workflow with intelligent automation.

---

## 🚀 **Current Features (Iteration 1)**

### **AI-Powered Tailoring**

- Upload your resume (PDF or DOCX)
- Paste or fetch a job description
- Automatically generate a tailored, ATS-friendly resume using GPT
- Preview and export the tailored resume as DOCX

### **Flexible Job Description Input**

- URL-based scraping (LinkedIn/ZipRecruiter/Indeed-compatible with headers)
- Manual paste mode for sites that block automated access

### **Modern GUI**

- PyQt6 desktop interface
- Dark theme
- Reusable components: file picker, settings panel, output panel
- Clean section-based layout for resume, job description, and output

### **Configurable Tailoring Options**

- Emphasize keywords
- Maintain approximate resume length
- Ensure ATS formatting

---

## 🛣️ **Roadmap**

### 🔜 **Iteration 2**

- **Page Length Enforcement (1–2 pages)**  
  Ensure the output resume fits standard U.S. letter formatting (8.5 x 11).

- **Job Tailoring Log System**  
  Store each tailored resume along with job title, company, and date.  
  View past tailoring history in a sortable table.

- **Accessibility Features**

  - Font size adjustments
  - High contrast modes
  - Screen reader-friendly mode

- **Personalization Panel**  
  Allow user to adjust tone, formality, skill emphasis, and layout preferences.

### 🔐 **Future Release**

- **Multi-User Authentication**

  - Local account system
  - Cloud sync for resume history, templates, and preferences

- **Advanced Resume Templates**

  - Profession-specific variations
  - Modern, minimalist, corporate, creative, and academic styles

- **Cover Letter Generator**

  - Auto-generate letters based on resume + job description

- **ATS Score Analyzer**

  - Keyword overlap
  - Missing skills
  - Strength meter

- **Job Board Integrations**
  - Direct import from LinkedIn, Indeed, ZipRecruiter, etc.

---

## 🧩 **Technical Overview**

### **Tech Stack**

- **Python 3.9+**
- **PyQt6** (GUI)
- **OpenAI Python SDK** (AI resume tailoring)
- **python-docx**, **pdfplumber** (document parsing)
- **BeautifulSoup4**, **requests** (job scraping)
- **dotenv** (environment config)
- **QSS (Qt Stylesheets)** for dark mode UI styling

---

## 📁 **Project Structure**

```bash
JobFit-Pro/
│
├── app/
│ ├── main.py
│ ├── window_main.py
│ ├── components/
│ │ ├── file_picker.py
│ │ ├── output_panel.py
│ │ └── settings_panel.py
│ ├── styles/
│ │ └── app.qss
│ └── ui/
│ ├── main_window.py
│ └── main_window.ui
│
├── core/
│ ├── extractor/
│ ├── processor/
│ └── exporter/
│
├── services/
│ ├── openai_client.py
│ └── config.py
│
├── tests/
├── assets/
├── requirements.txt
└── README.md
```

---

## ⚙️ **Setup Instructions**

### **1. Clone the repo**

```bash
git clone https://github.com/<your-username>/JobFit-Pro.git
cd JobFit-Pro
```

### **2. Create a virtual environment**

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### **3. Install dependencies**

```bash
pip install -r requirements.txt
```

### **4. Configure OpenAI**

Create a .env file in the project root.

```bash
OPENAI_API_KEY=your_api_key_here
```

### **5. Run the application**

```bash
python -m app.main
```

---

## Tests

Tests (coming soon) will live under
`tests/`  
Unit tests will cover:

- Resume parsing
- Job description extraction
- Tailoring engine
- Export logic

---

## Contributing

This project is currently private and under active development.  
Contribution guidelines and issue templates will be added as multi-user development begins.

---

## License

This project is proprietary and all rights are reserved.  
You may not copy, modify, or redistribute this software without explicit permission from the author.

---

## Contact

For questions or feature suggestions:  
Antonio Lee
GitHub: https://github.com/Techdudetony
