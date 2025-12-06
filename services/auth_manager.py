"""
AuthManager
-----------
Handles:
- Sign up
- Sign in
- Sign out
- Session persistence (local file)
- Auto-login using refresh tokens
"""

import os
import json
from supabase import create_client
from services.supabase_client import supabase


SESSION_FILE = ".auth_session.json"


class AuthManager:
    def __init__(self):
        self.session = None
        self.user = None

        # Attempt auto-login
        self.load_session_from_disk()

    # ----------------------------------------------------------------------
    # Session Persistence
    # ----------------------------------------------------------------------
    def save_session_to_disk(self, session):
        """Store refresh session locally."""
        try:
            with open(SESSION_FILE, "w") as f:
                json.dump(
                    {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                    },
                    f,
                    indent=4,
                )
        except Exception as e:
            print("[AUTH] Could not save session:", e)

    def load_session_from_disk(self):
        """Load previous session and validate/refresh."""
        if not os.path.exists(SESSION_FILE):
            return None

        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)

            refresh_token = data.get("refresh_token")
            if not refresh_token:
                return None

            # Attempt refresh
            resp = supabase.auth.refresh_session(refresh_token)
            if resp and resp.user:
                self.session = resp.session
                self.user = resp.user
                print("[AUTH] Auto-login successful.")
                return resp.user

        except Exception as e:
            print("[AUTH] Auto-login failed:", e)

        return None

    def clear_session_on_disk(self):
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except:
                pass

    # ----------------------------------------------------------------------
    #  AUTH ACTIONS
    # ----------------------------------------------------------------------
    def sign_up(self, email: str, password: str):
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            return response
        except Exception as e:
            print("[AUTH] Sign up failed:", e)
            return None

    def sign_in(self, email: str, password: str):
        try:
            response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if response and response.user:
                self.session = response.session
                self.user = response.user
                self.save_session_to_disk(response.session)
            return response
        except Exception as e:
            print("[AUTH] Sign in failed:", e)
            return None

    def sign_out(self):
        try:
            supabase.auth.sign_out()
        except:
            pass

        self.session = None
        self.user = None
        self.clear_session_on_disk()

    # ----------------------------------------------------------------------
    def get_user(self):
        """Return authenticated user or None."""
        if not self.session:
            return None

        try:
            resp = supabase.auth.get_user(self.session.access_token)
            self.user = resp.user
            return resp.user
        except:
            return None
