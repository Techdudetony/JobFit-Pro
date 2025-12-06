# services/auth_manager.py
"""
AuthManager
-----------
Thin wrapper around Supabase auth for the desktop app.

- Keeps track of the current session and user in this process
- Provides sign_up / sign_in / sign_out helpers
- Exposes a shared singleton: `auth`
"""

from typing import Optional
from supabase import Client
from services.supabase_client import supabase


class AuthManager:
    """
    Small stateful wrapper around `supabase.auth`.

    Important:
    - We rely on a single global instance `auth` (see bottom of file).
    - All parts of the app (AuthModal, MainWindow, etc.) must import
      and use this SAME instance for sign-in state to be shared.
    """

    def __init__(self) -> None:
        # Current Supabase session + user for this running app
        self.session = None
        self.user = None

    # ------------------------------------------------------------------
    # Sign Up
    # ------------------------------------------------------------------
    def sign_up(self, email: str, password: str):
        """
        Registers a new Supabase user account.

        Returns:
            The Supabase response object (with `.user`, `.session`, etc).
        """
        response = supabase.auth.sign_up({"email": email, "password": password})

        # We typically do NOT store session on sign-up because some
        # projects require email verification before login.
        return response

    # ------------------------------------------------------------------
    # Sign In
    # ------------------------------------------------------------------
    def sign_in(self, email: str, password: str):
        """
        Logs in an existing user via email + password.

        On success:
            - self.session is set
            - self.user is set
        Returns:
            The Supabase response object.
        """
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        # New supabase-py returns objects with .user and .session properties
        self.session = getattr(response, "session", None)
        self.user = getattr(response, "user", None)


        return response

    # ------------------------------------------------------------------
    # Current user
    # ------------------------------------------------------------------
    def get_user(self):
        """
        Returns the currently authenticated Supabase user object, or None.
        We keep this in memory only for this app run.
        """
        return self.user

    # ------------------------------------------------------------------
    # Sign out
    # ------------------------------------------------------------------
    def sign_out(self):
        """
        Clears Supabase session on the server side (if supported) and
        wipes our local session/user state.
        """
        try:
            supabase.auth.sign_out()
        except Exception as e:
            # Not fatal; just log it and clear local state
            print("Supabase sign_out error:", e)

        self.session = None
        self.user = None


# ----------------------------------------------------------------------
# Shared singleton instance used across the app
# ----------------------------------------------------------------------
auth = AuthManager()
