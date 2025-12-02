'''
Centralized configuration for API keys, environment variables, and application-wide constants.
'''
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-5.1"

if not API_KEY:
    raise ValueError(" OPENAI_API_KEY is missing. Add it to your .env file.")