# services/supabase_client.py
"""
Supabase client singleton

Responsible only for:
- Reading Supabase URL + KEY from environment variables
- Creating a single `supabase` client to be reused across the app
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Go up ONE level from services/ to reach the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(_get_base_dir(), ".env"))

# -------------------------------------------------------------------
# Read config from environment
# -------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase configuration missing. "
        "Set SUPABASE_URL and SUPABASE_ANON_KEY (or SUPABASE_SERVICE_ROLE_KEY)."
    )

# -------------------------------------------------------------------
# Create a single shared client
# -------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)