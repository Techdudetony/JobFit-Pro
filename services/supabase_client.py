# services/supabase_client.py
"""
Supabase client singleton

Responsible only for:
- Reading Supabase URL + KEY from environment variables
- Creating a single `supabase` client to be reused across the app
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# -------------------------------------------------------------------
# Read config from environment
# -------------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Prefer SERVICE_ROLE if you use it; otherwise fall back to ANON
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
