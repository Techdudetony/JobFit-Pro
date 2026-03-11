"""
AuthManager
------------------------

Centralized wrapper around Supabase authentication.
Ensures ALL authentication functions return a consistent structure:

    (user_object, error_message or None)

This keeps the AuthModal clean and predictable.

Handles:
- Sign Up
- Sign In
- Sign Out
- Session tracking
- Remember Me (secure token storage)
"""

from typing import Optional, Tuple
import keyring
import json
from services.supabase_client import supabase

# Keyring service name for secure storage
SERVICE_NAME = "JobFitPro"
CREDENTIALS_KEY = "saved_session"


class AuthManager:
    def __init__(self):
        # Track authenticated session + user
        self.session = None
        self.user = None

    # ==================================================================
    # SIGN UP
    # ==================================================================
    def sign_up(
        self, email: str, password: str
    ) -> Tuple[Optional[object], Optional[str]]:
        """
        Registers a new user account with Supabase.

        Returns:
            (user, None) on success
            (None, error_message) on failure

        NOTE:
        Supabase may require email confirmation depending on project settings.
        """
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})

            user = getattr(res, "user", None)
            error = getattr(res, "error", None)

            return user, error
        except Exception as e:
            # Surface meaningful errors to AuthModal
            return None, str(e)

    # ==================================================================
    # SIGN IN
    # ==================================================================
    def sign_in(
        self, email: str, password: str, remember_me: bool = False
    ) -> Tuple[Optional[object], Optional[str]]:
        """
        Logs in using email/password.

        Args:
            email: User's email
            password: User's password
            remember_me: If True, saves session tokens for auto-login

        Returns:
            (user, None) on success
            (None, error_message) on failure
        """
        try:
            res = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception as e:
            return None, str(e)

        # Extract session / user from response
        session = getattr(res, "session", None)
        user = getattr(res, "user", None)

        # Some Supabase Python client versions nest the user inside session
        if session and getattr(session, "user", None):
            user = session.user

        error = getattr(res, "error", None)

        # Cache state internally
        self.session = session
        self.user = user

        # CRITICAL FIX: Set the session token on the Supabase client
        # This ensures storage operations use the authenticated user's credentials
        if session and hasattr(session, "access_token"):
            supabase.auth.set_session(session.access_token, session.refresh_token)

            # Save session if "Remember Me" is enabled
            if remember_me:
                self._save_session(session)

        return user, error

    # ==================================================================
    # REMEMBER ME - Session Storage
    # ==================================================================
    def _save_session(self, session):
        """Securely save session tokens using keyring."""
        try:
            session_data = {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            }
            keyring.set_password(
                SERVICE_NAME, CREDENTIALS_KEY, json.dumps(session_data)
            )
            print("[AUTH] Session saved for Remember Me")
        except Exception as e:
            print(f"[AUTH] Failed to save session: {e}")

    def load_saved_session(self) -> Tuple[Optional[object], Optional[str]]:
        """
        Attempt to restore a saved session.

        Returns:
            (user, None) on success
            (None, error_message) on failure
        """
        try:
            # Retrieve saved session data
            saved_data = keyring.get_password(SERVICE_NAME, CREDENTIALS_KEY)
            if not saved_data:
                return None, "No saved session found"

            session_data = json.loads(saved_data)
            access_token = session_data.get("access_token")
            refresh_token = session_data.get("refresh_token")

            if not access_token or not refresh_token:
                return None, "Invalid session data"

            # Restore session with Supabase
            supabase.auth.set_session(access_token, refresh_token)

            # Get current user
            response = supabase.auth.get_user()
            user = getattr(response, "user", None)

            if not user:
                # Session expired or invalid
                self.clear_saved_session()
                return None, "Session expired"

            # Update internal state
            self.user = user
            self.session = response

            print(f"[AUTH] Successfully restored session for {user.email}")
            return user, None

        except Exception as e:
            print(f"[AUTH] Failed to restore session: {e}")
            self.clear_saved_session()
            return None, str(e)

    def clear_saved_session(self):
        """Remove saved session credentials."""
        try:
            keyring.delete_password(SERVICE_NAME, CREDENTIALS_KEY)
            print("[AUTH] Saved session cleared")
        except keyring.errors.PasswordDeleteError:
            # No saved session to delete
            pass
        except Exception as e:
            print(f"[AUTH] Error clearing session: {e}")

    def has_saved_session(self) -> bool:
        """Check if there's a saved session available."""
        try:
            saved_data = keyring.get_password(SERVICE_NAME, CREDENTIALS_KEY)
            return saved_data is not None
        except:
            return False

    # ==================================================================
    def get_user(self):
        """Returns the currently authenticated user (or None)."""
        return self.user

    # ==================================================================
    def get_session(self):
        """Returns the current session (or None)."""
        return self.session

    # ==================================================================
    def sign_out(self, clear_remember_me: bool = True):
        """
        Logs out and clears local session tracking.

        Args:
            clear_remember_me: If True, also clears saved session
        """
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print("Supabase sign_out error:", e)

        self.session = None
        self.user = None

        if clear_remember_me:
            self.clear_saved_session()


# Singleton instance used throughout the application
auth = AuthManager()
