from services.supabase_client import supabase


class AuthManager:
    def __init__(self):
        self.session = None
        self.user = None

    # -------------------------------
    def sign_up(self, email: str, password: str):
        return supabase.auth.sign_up({"email": email, "password": password})

    # -------------------------------
    def sign_in(self, email: str, password: str):
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        self.session = response.session
        self.user = response.user
        return response

    # -------------------------------
    def get_user(self):
        """
        Always returns the currently authenticated user.
        If session expired, attempts to use Supabase's built-in recovery.
        """
        try:
            response = supabase.auth.get_user()
            return response.user
        except Exception:
            return None

    # -------------------------------
    def sign_out(self):
        supabase.auth.sign_out()
        self.session = None
        self.user = None
