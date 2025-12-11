"""
SessionState
------------

Central in-memory store for the user’s working data during a
JobFit Pro session. Designed to be lightweight, serializable,
and UI-agnostic.
"""

import json
import os
from datetime import datetime


class SessionState:
    SESSION_FILE = "session_state.json"  # stored in working directory

    def __init__(self):
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""
        self.loaded_resume_path = ""
        self.job_url = ""
        self.last_updated = None

    # ----------------------------------------------------------
    # Helper: mark session as changed
    # ----------------------------------------------------------
    def touch(self):
        self.last_updated = datetime.now().isoformat()

    # ----------------------------------------------------------
    # Reset state
    # ----------------------------------------------------------
    def clear(self):
        self.resume_text = ""
        self.job_text = ""
        self.tailored_text = ""
        self.loaded_resume_path = ""
        self.job_url = ""
        self.last_updated = None

    # ----------------------------------------------------------
    # Change detection
    # ----------------------------------------------------------
    def is_empty(self) -> bool:
        """Return True if no data is currently loaded."""
        return not any(
            [
                self.resume_text,
                self.job_text,
                self.tailored_text,
                self.loaded_resume_path,
                self.job_url,
            ]
        )

    # ----------------------------------------------------------
    # Save session to disk
    # ----------------------------------------------------------
    def save(self):
        data = {
            "resume_text": self.resume_text,
            "job_text": self.job_text,
            "tailored_text": self.tailored_text,
            "loaded_resume_path": self.loaded_resume_path,
            "job_url": self.job_url,
            "last_updated": self.last_updated,
        }

        with open(self.SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ----------------------------------------------------------
    # Load session from disk (if exists)
    # ----------------------------------------------------------
    def load(self):
        if not os.path.exists(self.SESSION_FILE):
            return False

        try:
            with open(self.SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.resume_text = data.get("resume_text", "")
            self.job_text = data.get("job_text", "")
            self.tailored_text = data.get("tailored_text", "")
            self.loaded_resume_path = data.get("loaded_resume_path", "")
            self.job_url = data.get("job_url", "")
            self.last_updated = data.get("last_updated", None)

            return True

        except Exception as e:
            print("[SESSION LOAD ERROR]", e)
            return False
