# JobFit Pro

> AI-powered resume tailoring for Windows — built with Python, PyQt6, and OpenAI.

JobFit Pro is a modern desktop application that helps job seekers tailor their resumes to specific job descriptions in seconds. It parses your resume, analyzes job postings, and uses GPT to generate a professionally aligned, ATS-optimized version — all from a clean tabbed interface with cloud sync.

---

## Features

### AI Resume Tailoring
- Upload your resume (PDF or DOCX)
- Paste or fetch a job description by URL
- Generate a tailored, ATS-friendly resume using OpenAI GPT
- Export the result as DOCX or PDF

### ATS Score Analysis
- Keyword overlap scoring between resume and job description
- AI-powered breakdown of missing skills, tone, and alignment
- AI-written content detection and integrity check
- Sliding ATS panel with animated score bar and sidebar badge notification

### Cover Letter Generator
- Auto-generate cover letters from your resume + job description
- Choose tone (Professional / Friendly / Confident / Creative) and length
- Source selected automatically: uses tailored resume if available, uploaded resume if not, or prompts to upload if neither exists
- Editable output with export to DOCX/PDF
- Cover letters saved to tailoring history

### Tailoring History
- Every tailoring session is saved locally (JSON + PDF)
- View company, role, ATS score, and cover letter per entry
- Replay ATS analysis on any past resume
- Edit company/role fields inline
- Bulk or single-row delete

### Cloud Sync
- All history synced to Supabase on each tailoring session
- Manual Push All to Cloud and Pull from Cloud in Settings
- User preferences (theme, tailoring defaults) synced across devices
- Local-first — app works offline, syncs when connected

### Authentication
- Email/password sign-in and sign-up
- Remember Me with secure keyring token storage
- Grace period (30-minute session restoration on restart)
- Auto-login on launch when session is valid

### Modern UI
- Tabbed sidebar layout: Tailor, History, Settings, Cover Letter
- Dark and light theme with live toggle
- Toast notifications for async events (ATS score, errors)
- Onboarding tutorial on first launch (re-triggerable from Help menu)
- Keyboard shortcuts for all major actions

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | PyQt6 |
| AI Engine | OpenAI GPT (gpt-4.1 default) |
| Auth & Storage | Supabase (PostgreSQL + Storage) |
| Resume Parsing | pdfplumber, python-docx |
| Job Scraping | BeautifulSoup4, requests |
| Credentials | keyring |
| Packaging | PyInstaller |
| Styling | QSS (Qt Stylesheets) |

---

## Project Structure

```
JobFit-Pro/
├── app/
│   ├── main.py                        # Entry point
│   ├── window_main.py                 # Main window controller
│   ├── components/
│   │   ├── file_picker.py             # Reusable file picker widget
│   │   ├── output_panel.py            # Formatted resume output panel
│   │   └── settings_panel.py          # Tailoring options checkboxes
│   ├── data/
│   │   ├── tailoring_history.json     # Local history store
│   │   └── history_resumes/           # Saved tailored resume PDFs
│   ├── state/
│   │   └── session_state.py
│   ├── styles/
│   │   ├── app.qss                    # Dark theme stylesheet
│   │   └── app_light.qss              # Light theme stylesheet
│   └── ui/
│       ├── auth_modal.py              # Sign in / sign up dialog
│       ├── main_window_ui.py
│       ├── main_window.py             # UI layout definition
│       ├── main_window.ui
│       ├── onboarding.py              # First-launch tutorial overlay
│       ├── sidebar_nav.py             # Tab sidebar with badge support
│       ├── ats_panel.py               # Sliding ATS score drawer
│       ├── toast_notification.py      # Animated toast messages
│       ├── tailoring_history_window.py
│       ├── dialogs/
│       │   ├── about_dialog.py
│       │   ├── help_dialog.py
│       │   └── loading_dialog.py
│       └── tabs/
│           ├── tab_tailor.py          # Main tailoring tab
│           ├── tab_history.py         # History browser tab
│           ├── tab_settings.py        # Settings + Cloud Sync tab
│           └── tab_cover_letter.py    # Cover letter generator tab
│
├── core/
│   ├── extractor/
│   │   ├── pdf_parser.py              # PDF text extraction
│   │   ├── docx_parser.py             # DOCX text extraction
│   │   └── job_parser.py              # Job description URL scraper
│   ├── history/
│   │   ├── history_manager.py
│   │   └── utils.py
│   ├── processor/
│   │   ├── tailor_engine.py           # GPT resume tailoring engine
│   │   ├── cleaner.py                 # Resume text normalization
│   │   ├── keyword_matcher.py         # ATS keyword overlap scoring
│   │   ├── keyword_analyzer.py        # AI-powered ATS breakdown
│   │   ├── ai_detector.py             # AI-written content detection
│   │   ├── job_meta_extractor.py      # Company/role extraction from JD
│   │   └── cover_letter_engine.py     # GPT cover letter generation
│   ├── uploader/
│   │   └── supabase_uploader.py       # Resume upload to Supabase Storage
│   ├── utils/
│   │   └── validators.py
│   └── exporter/
│       ├── docx_builder.py            # DOCX export with ATS formatting
│       └── pdf_exporter.py            # PDF export via docx2pdf
│
├── services/
│   ├── config.py                      # .env loader (API keys, model)
│   ├── openai_client.py               # OpenAI API wrapper
│   ├── auth_manager.py                # Supabase auth + Remember Me
│   ├── supabase_client.py             # Supabase client singleton
│   ├── theme_manager.py               # Light/dark theme switching
│   └── sync_manager.py                # Cloud sync workers (history + prefs)
│
├── tests/                             # Unit tests (in progress)
├── assets/
│   └── icons/                         # SVG icons for UI
├── .env                               # API keys (not committed)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Techdudetony/JobFit-Pro.git
cd JobFit-Pro
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-4.1
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

You can also configure the API key and model directly from **Settings → API Configuration** inside the app.

### 5. Run the app

```bash
python -m app.main
```

---

## Build (Windows .exe)

```bash
pyinstaller --noconfirm --onefile --windowed \
  --name "JobFit Pro" \
  --icon "assets/desktop_icon.ico" \
  --add-data "app/styles/app.qss;app/styles" \
  --add-data "app/styles/app_light.qss;app/styles" \
  --add-data "assets;assets" \
  --add-data "assets/icons;assets/icons" \
  --collect-all openai \
  --collect-all pdfplumber \
  --collect-all supabase \
  --hidden-import=PyQt6.sip \
  --hidden-import=PyQt6.QtSvg \
  app/main.py

copy .env dist\.env
```

---

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Tailor resume | Ctrl+T |
| Fetch job description | Ctrl+F |
| Load resume | Ctrl+O |
| Export DOCX | Ctrl+E |
| Export PDF | Ctrl+Shift+E |
| Open history | Ctrl+H |
| New session | Ctrl+N |
| Quit | Ctrl+Q |

---

## Roadmap

### In Progress
- Resizable panels (QSplitter)
- Tone analyzer badge
- Interview prep mode

### Planned
- Multi-resume profiles
- Resume builder with manual entry form
- Resume versioning with diff view
- Skills bank with proficiency badges
- Resume templates (modern, minimal, corporate)
- Usage dashboard
- Help wiki

---

## License

Proprietary — all rights reserved.
You may not copy, modify, or redistribute this software without explicit written permission from the author.

---

## Author

Antonio Lee — [GitHub: Techdudetony](https://github.com/Techdudetony)