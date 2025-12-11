"""
Global configuration for environment-driven constants.

This module loads environment variables from `.env` and exposes
centralized settings used across the application.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# OpenAI Configuration
# ---------------------------------------------------------

API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-5.2")

if not API_KEY:
    raise ValueError(" OPENAI_API_KEY is missing. Add it to your .env file.")
