"""
AuthManager
----------------------------------
Thin wrapper around Supabase authentication for JobFit Pro.

- Maintains the current user & session for the running app
- Provides simple sign-up / sign-in / sign-out helpers
- Wraps Supabase auth calls with basic error handling
- Exposes a shared singleton instance: `auth`
"""

from typing import Optional, Any, Dict
from services.supabase_client import supabase


class AuthManager:
    def __init__(self) -> None:
        self.session = None
        self.user = None

    # -------------------------------------------------------
    # SIGN UP
    # -------------------------------------------------------
    def sign_up(self, email: str, password: str) -> Any:
        try:
            return supabase.auth.sign_up({"email": email, "password": password})
        except Exception as e:
            return {"error": str(e)}

    # -------------------------------------------------------
    # SIGN IN
    # -------------------------------------------------------
    def sign_in(self, email: str, passsword: str) -> Any:
        try:
            response = supabase.auth.sign_in_with_password(
                {"email": email, "password": passsword}
            )
        except Exception as e:
            return {"error": str(e), "user": None, "session": None}

        # Extract user + session safely
        session = getattr(response, "session", None)
        user = getattr(response, "user", None)

        # For some SDK versions that nest user inside session
        if session and getattr(session, "user", None):
            user = session.user

        self.session = session
        self.user = user

        return response

    # -------------------------------------------------------
    # GET USER
    # -------------------------------------------------------
    def get_user(self):
        return self.user

    # -------------------------------------------------------
    # SIGN OUT
    # -------------------------------------------------------
    def sign_out(self):
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print("Supabase sign_out error:", e)

        # Always clear local session
        self.session = None
        self.user = None


# Shared global instance
auth = AuthManager()
