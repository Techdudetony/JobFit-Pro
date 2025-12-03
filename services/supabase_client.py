# services/supabase_client.py

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# --- LOAD .env from project root ---
load_dotenv()

# --- Fetch env vars AFTER loading env file ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# --- Safety check instead of crashing ---
if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n[SUPABASE INIT ERROR] Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env\n")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
