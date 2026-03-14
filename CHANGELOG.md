# Changelog

All notable changes to JobFit Pro are documented here.

---

## [2.0.0] — 2026-03-12

### Added

**UI / Layout**
- Replaced flat single-window layout with tabbed sidebar (Tailor, History, Settings, Cover Letter)
- `SidebarNav` component with icon tabs, active highlight, and red dot badge support
- Animated loading overlay anchored to main window (replaces modal dialog)
- `ToastNotification` — frameless slide-up toast for async events with 4 presets (success, warning, error, info)
- Onboarding tutorial overlay (8-step, spotlight-based) shown on first launch; re-triggerable from Help menu
- Keyboard shortcuts: Ctrl+T (Tailor), Ctrl+F (Fetch), Ctrl+O (Load), Ctrl+E/Ctrl+Shift+E (Export), Ctrl+H (History), Ctrl+N (New), Ctrl+Q (Quit)
- Light theme (`app_light.qss`) with live toggle from View menu and Settings tab
- Theme preference persisted to `theme_preference.json`
- Enter key submits sign-in form

**ATS Score Analysis**
- `ATSPanel` — sliding drawer panel with animated score bar, keyword breakdown, missing skills, and tone analysis
- `KeywordAnalyzer` — AI-powered OpenAI breakdown replacing simple keyword counter
- `AIDetector` — detects AI-written content in submitted resume; warns user before tailoring
- ATS analysis runs async after tailoring completes (200ms delay) so resume appears immediately
- Toast notification fires with color-coded score when ATS analysis finishes
- Sidebar badge appears on ATS tab after new analysis; clears on tab visit
- ATS result stored in tailoring history entry

**Cover Letter Generator**
- New Cover Letter tab with tone selector (Professional / Conversational / Enthusiastic)
- Length selector (Short / Medium / Long)
- Source toggle — use original resume or tailored resume as input
- Editable output `QTextEdit` (user can refine before exporting)
- Export to DOCX and PDF
- Cover letter saved to tailoring history on generation

**Tailoring History**
- History entries now include: `company`, `role`, `job_url`, `resume_url`, `local_pdf`, `ats_result`, `cover_letter`, `timestamp`, `last_updated`
- Company and role extracted automatically from job description via `JobMetaExtractor` (OpenAI-assisted)
- Tailored resume saved as local PDF in `app/data/history_resumes/`
- ATS replay — re-run analysis on any past entry from History tab
- Cover letter view dialog per entry (editable, copyable)
- Inline editing of company, role fields with auto-save

**Authentication**
- Remember Me checkbox on sign-in with secure `keyring` token storage
- Grace period: session restored automatically within 30 minutes of app close
- Auto-login on launch when valid session found — skips modal entirely
- Sign Out dialog with "Forget this device" checkbox

**Cloud Sync**
- `SyncManager` with background `QThread` workers for all Supabase operations
- `tailoring_history` Supabase table — upsert on `(user_id, timestamp)`, safe to re-push
- `user_preferences` Supabase table — theme and settings panel state per user
- On login: pulls preferences and history from cloud, merges with local (newer `last_updated` wins)
- On each tailor session: pushes history entry to Supabase async
- On ATS complete: patches `ats_result` into latest history entry and pushes update
- On cover letter generated: patches `cover_letter` into latest history entry and pushes update
- Manual **Push All to Cloud** and **Pull from Cloud** buttons in Settings tab
- Last synced timestamp displayed and persisted in `~/.jobfitpro/config.json`
- Save Preferences now pushes to Supabase immediately

**Settings Tab**
- API key input (masked, show/hide toggle) writes directly to `.env`
- Model selector dropdown (gpt-4.1, gpt-4.1-mini, gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo)
- Theme toggle button
- Default tailoring preferences with live apply to Tailor tab
- Cloud Sync group with push, pull, and last-synced status

### Changed
- `TailoringWorker` moved to `window_main.py` as a dedicated `QThread` subclass
- `HistoryManager` now used for all history reads/writes (replaces ad-hoc JSON access)
- `ResumeTailor.generate()` accepts `limit_one_page` alias for backward compatibility
- `OutputPanel` upgraded from `QPlainTextEdit` to `QTextEdit` with HTML resume formatting
- Auth flow moved entirely to `AuthManager` singleton; `AuthModal` is UI-only
- `ThemeManager` initialized in `main.py` before `MainWindow` to prevent style flash

### Fixed
- Settings key mismatch between `SettingsPanel` and `SettingsResult` (`limit_one` vs `limit_one_page`)
- Mutually exclusive page-limit checkboxes (`chk_limit_pages` / `chk_limit_one`)
- Delete index drift in history window after row removal
- OpenAI model name corrected in `config.py`
- PyInstaller path resolution via `sys._MEIPASS` for stylesheets, icons, and `.env`
- `--collect-all` flags added for `openai`, `pdfplumber`, `supabase` in build command
- Supabase SDK v2 response handling (`res.data`, `res.user` attribute access)
- `AuthManager` used as singleton throughout — prevents auth state fragmentation
- ATS result not stored in history due to async timing (moved patch to `_on_ats_ready`)
- Settings tab checkboxes not reflecting cloud preferences on login
- `user_preferences` not updating when Save Preferences clicked (now pushes to Supabase)
- `tailoring_history` table missing `timestamp`, `last_updated`, and other columns (migration SQL added)

---

## [1.0.0] — 2025-12

### Added
- Initial release
- PyQt6 desktop application with three-column layout (Job / Resume / Output)
- Resume upload (PDF and DOCX) with `pdfplumber` and `python-docx` parsers
- Job description fetch by URL using BeautifulSoup4
- Manual job description paste mode
- AI resume tailoring via OpenAI GPT (`ResumeTailor`)
- Tailoring options: emphasize keywords, keep length, ATS-friendly, page limit
- Export tailored resume to DOCX (`docx_builder.py`)
- Export tailored resume to PDF via `docx2pdf`
- Basic tailoring history (local JSON)
- Supabase authentication (sign-in / sign-up)
- Supabase Storage upload for tailored resumes
- Dark theme (`app.qss`)
- `FilePicker`, `SettingsPanel`, `OutputPanel` reusable components
- `LoadingDialog` with animated progress bar during AI processing
- `HelpDialog` with tabbed user guide, tailoring explanation, and about page
- `AboutDialog` with version and tech stack info