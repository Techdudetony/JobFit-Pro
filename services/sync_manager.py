# services/sync_manager.py
"""
SyncManager — JobFit Pro
-------------------------

Handles all bidirectional sync between local JSON/files and Supabase.

Strategy: LOCAL-FIRST
  - All writes go to local JSON immediately (app works offline)
  - Supabase pushes/pulls happen in background QThreads
  - On login: pull cloud → merge with local (newer last_updated wins)
  - On new history entry: push to Supabase async
  - On preference change: push to Supabase async

Tables:
  - tailoring_history  (id, user_id, company, role, job_url, resume_url,
                        local_pdf, cover_letter, ats_result, timestamp,
                        last_updated, created_at)
  - user_preferences   (user_id, theme, settings, updated_at)
"""

import json
import os
from datetime import datetime, timezone

from PyQt6.QtCore import QThread, pyqtSignal

from services.supabase_client import supabase
from services.auth_manager import auth


# ==================================================================
# Worker: Push a single history entry to Supabase
# ==================================================================
class PushHistoryWorker(QThread):
    finished = pyqtSignal(str)  # emits the Supabase row id on success
    error = pyqtSignal(str)

    def __init__(self, entry: dict):
        super().__init__()
        self.entry = entry

    def run(self):
        try:
            user = auth.get_user()
            if not user:
                self.error.emit("Not authenticated")
                return

            row = _entry_to_row(self.entry, user.id)

            # Upsert by (user_id, timestamp) — safe to re-push without duplication
            res = (
                supabase.table("tailoring_history")
                .upsert(
                    row,
                    on_conflict="user_id,timestamp",
                )
                .execute()
            )

            rows = getattr(res, "data", None) or []
            if rows:
                self.finished.emit(rows[0].get("id", ""))
            else:
                self.error.emit("Upsert returned no data")

        except Exception as e:
            self.error.emit(str(e))


# ==================================================================
# Worker: Pull history from Supabase and merge with local
# ==================================================================
class PullHistoryWorker(QThread):
    finished = pyqtSignal(list)  # emits merged history list
    error = pyqtSignal(str)

    def __init__(self, local_history: list):
        super().__init__()
        self.local_history = local_history

    def run(self):
        try:
            user = auth.get_user()
            if not user:
                self.error.emit("Not authenticated")
                return

            res = (
                supabase.table("tailoring_history")
                .select("*")
                .eq("user_id", user.id)
                .order("timestamp", desc=True)
                .execute()
            )

            cloud_rows = getattr(res, "data", None) or []
            cloud_entries = [_row_to_entry(r) for r in cloud_rows]

            merged = _merge_histories(self.local_history, cloud_entries)
            self.finished.emit(merged)

        except Exception as e:
            self.error.emit(str(e))


# ==================================================================
# Worker: Push user preferences to Supabase
# ==================================================================
class PushPrefsWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, theme: str, settings: dict):
        super().__init__()
        self.theme = theme
        self.settings = settings

    def run(self):
        try:
            user = auth.get_user()
            if not user:
                self.error.emit("Not authenticated")
                return

            row = {
                "user_id": user.id,
                "theme": self.theme,
                "settings": self.settings,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            supabase.table("user_preferences").upsert(
                row, on_conflict="user_id"
            ).execute()

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


# ==================================================================
# Worker: Pull user preferences from Supabase
# ==================================================================
class PullPrefsWorker(QThread):
    finished = pyqtSignal(dict)  # emits {"theme": ..., "settings": {...}}
    error = pyqtSignal(str)

    def run(self):
        try:
            user = auth.get_user()
            if not user:
                self.error.emit("Not authenticated")
                return

            res = (
                supabase.table("user_preferences")
                .select("*")
                .eq("user_id", user.id)
                .single()
                .execute()
            )

            row = getattr(res, "data", None)
            if row:
                self.finished.emit(
                    {
                        "theme": row.get("theme", "dark"),
                        "settings": row.get("settings", {}),
                    }
                )
            else:
                # No prefs row yet — first time on this PC
                self.finished.emit({})

        except Exception as e:
            # PostgREST returns 406 when .single() finds no row — treat as empty
            self.finished.emit({})


# ==================================================================
# Public helpers called from window_main
# ==================================================================


class SyncManager:
    """
    Thin coordinator that owns worker references so they don't get
    garbage-collected before finishing.
    """

    def __init__(self):
        self._push_workers: list = []
        self._pull_worker = None
        self._prefs_push = None
        self._prefs_pull = None

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def push_history_entry(self, entry: dict, on_done=None, on_error=None):
        """Push a single history entry to Supabase in the background."""
        w = PushHistoryWorker(entry)
        if on_done:
            w.finished.connect(on_done)
        if on_error:
            w.error.connect(on_error)
        w.error.connect(lambda e: print(f"[SYNC] push error: {e}"))
        w.finished.connect(lambda _: self._push_workers.remove(w))
        self._push_workers.append(w)
        w.start()

    def pull_and_merge_history(self, local_history: list, on_done=None, on_error=None):
        """
        Pull cloud history and merge with local.
        on_done receives the merged list — caller saves it to disk.
        """
        w = PullHistoryWorker(local_history)
        if on_done:
            w.finished.connect(on_done)
        if on_error:
            w.error.connect(on_error)
        w.error.connect(lambda e: print(f"[SYNC] pull error: {e}"))
        self._pull_worker = w
        w.start()

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------
    def push_preferences(self, theme: str, settings: dict, on_done=None, on_error=None):
        """Push theme + settings panel state to Supabase."""
        w = PushPrefsWorker(theme, settings)
        if on_done:
            w.finished.connect(on_done)
        if on_error:
            w.error.connect(on_error)
        w.error.connect(lambda e: print(f"[SYNC] prefs push error: {e}"))
        self._prefs_push = w
        w.start()

    def pull_preferences(self, on_done=None, on_error=None):
        """Pull theme + settings from Supabase."""
        w = PullPrefsWorker()
        if on_done:
            w.finished.connect(on_done)
        if on_error:
            w.error.connect(on_error)
        w.error.connect(lambda e: print(f"[SYNC] prefs pull error: {e}"))
        self._prefs_pull = w
        w.start()


# ==================================================================
# Conversion helpers
# ==================================================================


def _entry_to_row(entry: dict, user_id: str) -> dict:
    """Convert local history dict → Supabase table row."""
    return {
        "user_id": user_id,
        "company": entry.get("company", ""),
        "role": entry.get("role", ""),
        "job_url": entry.get("job_url", ""),
        "resume_url": entry.get("resume_url", ""),
        "local_pdf": entry.get("local_pdf", ""),
        "cover_letter": entry.get("cover_letter", ""),
        "ats_result": entry.get("ats_result"),  # already dict or None
        "timestamp": entry.get("timestamp", ""),
        "last_updated": entry.get("last_updated", ""),
    }


def _row_to_entry(row: dict) -> dict:
    """Convert Supabase row → local history dict format."""
    return {
        "user_id": row.get("user_id", ""),
        "company": row.get("company", ""),
        "role": row.get("role", ""),
        "job_url": row.get("job_url", ""),
        "resume_url": row.get("resume_url", ""),
        "local_pdf": row.get("local_pdf", ""),
        "cover_letter": row.get("cover_letter", ""),
        "ats_result": row.get("ats_result"),
        "timestamp": row.get("timestamp", ""),
        "last_updated": row.get("last_updated", ""),
    }


def _merge_histories(local: list, cloud: list) -> list:
    """
    Merge local and cloud history lists.
    Key = timestamp (unique per tailoring session).
    Newer last_updated wins when both sides have the same timestamp.
    Preserves local_pdf paths from local entries (cloud won't have them).
    """
    index: dict = {}

    for entry in local:
        key = entry.get("timestamp", "")
        if key:
            index[key] = entry

    for cloud_entry in cloud:
        key = cloud_entry.get("timestamp", "")
        if not key:
            continue

        if key not in index:
            # New entry from cloud — add it
            index[key] = cloud_entry
        else:
            local_entry = index[key]
            local_updated = local_entry.get("last_updated", "")
            cloud_updated = cloud_entry.get("last_updated", "")

            if cloud_updated and cloud_updated > local_updated:
                # Cloud is newer — merge but keep local_pdf if present
                merged = {**cloud_entry}
                if local_entry.get("local_pdf"):
                    merged["local_pdf"] = local_entry["local_pdf"]
                index[key] = merged

    # Sort by timestamp descending (newest first)
    merged_list = sorted(
        index.values(),
        key=lambda e: e.get("timestamp", ""),
        reverse=True,
    )

    return merged_list


# Singleton
sync_manager = SyncManager()
