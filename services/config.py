"""
Centralized configuration for API keys, environment variables, and application-wide constants.
"""
import os
import sys
from dotenv import load_dotenv

def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Go up ONE level from services/ to reach the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(_get_base_dir(), ".env"))

API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-5.2"

if not API_KEY:
    raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file.")