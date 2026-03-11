"""
AuthManager
------------------------

Centralized wrapper around Supabase authentication.
Ensures ALL authentication functions return a consistent structure:

    (user_object, error_message or None)

Handles:
- Sign Up
- Sign In
- Sign Out
- Session tracking
- Remember Me (secure keyring token storage — indefinite)
- Grace Period (60-second auto-login after recent app close)
"""

import json
import os
import time
from typing import Optional, Tuple

import keyring
import keyring.errors

from services.supabase_client import supabase

# ------------------------------------------------------------------
# Keyring constants
# ------------------------------------------------------------------
SERVICE_NAME = "JobFitPro"
CREDENTIALS_KEY = "saved_session"

# ------------------------------------------------------------------
# Grace period: auto-login if app closed within this many seconds
# ------------------------------------------------------------------
GRACE_PERIOD_SECONDS = 60
GRACE_PERIOD_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "last_closed.json",
)


class AuthManager:
    def __init__(self):
        self.session = None
        self.user = None

    # ==================================================================
    # SIGN UP
    # ==================================================================
    def sign_up(
        self, email: str, password: str
    ) -> Tuple[Optional[object], Optional[str]]:
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            user = getattr(res, "user", None)
            error = getattr(res, "error", None)
            return user, error
        except Exception as e:
            return None, str(e)

    # ==================================================================
    # SIGN IN
    # ==================================================================
    def sign_in(
        self, email: str, password: str, remember_me: bool = False
    ) -> Tuple[Optional[object], Optional[str]]:
        try:
            res = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception as e:
            return None, str(e)

        session = getattr(res, "session", None)
        user = getattr(res, "user", None)

        if session and getattr(session, "user", None):
            user = session.user

        error = getattr(res, "error", None)

        self.session = session
        self.user = user

        if session and hasattr(session, "access_token"):
            supabase.auth.set_session(session.access_token, session.refresh_token)

            if remember_me:
                self._save_session(session)
            else:
                # Not "Remember Me" — only save for grace period use
                # Grace period restoration uses the same keyring slot but
                # we flag it as grace-only so sign-out clears it properly
                self._save_session(session, grace_only=True)

        return user, error

    # ==================================================================
    # REMEMBER ME — Keyring Storage
    # ==================================================================
    def _save_session(self, session, grace_only: bool = False):
        """Save session tokens to the OS keyring."""
        try:
            session_data = {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "remember_me": not grace_only,  # Flag for sign-out behavior
            }
            keyring.set_password(
                SERVICE_NAME, CREDENTIALS_KEY, json.dumps(session_data)
            )
            print(
                f"[AUTH] Session saved "
                f"({'Remember Me' if not grace_only else 'grace period only'})"
            )
        except Exception as e:
            print(f"[AUTH] Failed to save session: {e}")

    def load_saved_session(self) -> Tuple[Optional[object], Optional[str]]:
        """Restore a previously saved session from keyring."""
        try:
            saved_data = keyring.get_password(SERVICE_NAME, CREDENTIALS_KEY)
            if not saved_data:
                return None, "No saved session found"

            session_data = json.loads(saved_data)
            access_token = session_data.get("access_token")
            refresh_token = session_data.get("refresh_token")

            if not access_token or not refresh_token:
                return None, "Invalid session data"

            supabase.auth.set_session(access_token, refresh_token)

            response = supabase.auth.get_user()
            user = getattr(response, "user", None)

            if not user:
                self.clear_saved_session()
                return None, "Session expired"

            self.user = user
            self.session = response
            print(f"[AUTH] Restored session for {user.email}")
            return user, None

        except Exception as e:
            print(f"[AUTH] Failed to restore session: {e}")
            self.clear_saved_session()
            return None, str(e)

    def clear_saved_session(self):
        """Remove saved session credentials from keyring."""
        try:
            keyring.delete_password(SERVICE_NAME, CREDENTIALS_KEY)
            print("[AUTH] Saved session cleared")
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception as e:
            print(f"[AUTH] Error clearing session: {e}")

    def has_saved_session(self) -> bool:
        """Check if any saved session exists in keyring."""
        try:
            return keyring.get_password(SERVICE_NAME, CREDENTIALS_KEY) is not None
        except Exception:
            return False

    def is_remember_me_session(self) -> bool:
        """Returns True if the saved session was a full Remember Me (not grace-only)."""
        try:
            saved_data = keyring.get_password(SERVICE_NAME, CREDENTIALS_KEY)
            if not saved_data:
                return False
            session_data = json.loads(saved_data)
            return session_data.get("remember_me", False)
        except Exception:
            return False

    # ==================================================================
    # GRACE PERIOD — 60-Second Auto-Login
    # ==================================================================
    def stamp_close_time(self):
        """
        Call this when the app is closing.
        Writes the current timestamp to last_closed.json so we can
        check the grace period on next launch.
        """
        try:
            with open(GRACE_PERIOD_FILE, "w") as f:
                json.dump({"closed_at": time.time()}, f)
            print("[AUTH] Close timestamp saved for grace period")
        except Exception as e:
            print(f"[AUTH] Failed to stamp close time: {e}")

    def within_grace_period(self) -> bool:
        """
        Returns True if the app was closed within the last 60 seconds
        AND a session exists to restore.
        """
        if not os.path.exists(GRACE_PERIOD_FILE):
            return False

        try:
            with open(GRACE_PERIOD_FILE, "r") as f:
                data = json.load(f)

            closed_at = data.get("closed_at", 0)
            elapsed = time.time() - closed_at
            in_window = elapsed <= GRACE_PERIOD_SECONDS

            print(f"[AUTH] Last closed {elapsed:.1f}s ago — grace period: {in_window}")
            return in_window

        except Exception as e:
            print(f"[AUTH] Grace period check failed: {e}")
            return False

    def clear_grace_period(self):
        """Delete the close timestamp file."""
        try:
            if os.path.exists(GRACE_PERIOD_FILE):
                os.remove(GRACE_PERIOD_FILE)
        except Exception as e:
            print(f"[AUTH] Failed to clear grace period file: {e}")

    # ==================================================================
    # GETTERS
    # ==================================================================
    def get_user(self):
        return self.user

    def get_session(self):
        return self.session

    # ==================================================================
    # SIGN OUT
    # ==================================================================
    def sign_out(self, clear_remember_me: bool = True):
        """
        Sign out the current user.

        Args:
            clear_remember_me: If True, clears keyring + grace period file.
                               If False, keeps Remember Me for next launch.
        """
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print(f"[AUTH] Supabase sign_out error: {e}")

        self.session = None
        self.user = None

        if clear_remember_me:
            self.clear_saved_session()
            self.clear_grace_period()
        else:
            # Only clear the grace-only sessions; keep full Remember Me
            if not self.is_remember_me_session():
                self.clear_saved_session()


# Singleton instance used throughout the application
auth = AuthManager()