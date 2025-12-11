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
"""

from typing import Optional, Tuple
from services.supabase_client import supabase


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
        self, email: str, password: str
    ) -> Tuple[Optional[object], Optional[str]]:
        """
        Logs in using email/password.

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

        return user, error

    # ==================================================================
    def get_user(self):
        """Returns the currently authenticated user (or None)."""
        return self.user

    # ==================================================================
    def sign_out(self):
        """Logs out and clears local session tracking."""
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print("Supabase sign_out error:", e)

        self.session = None
        self.user = None


# Singleton instance used throughout the application
auth = AuthManager()
