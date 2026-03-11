"""
Wrapper around the OpenAI API to keep our code modular, testable, and easy to swap later.
"""

from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
from services.config import API_KEY, MODEL_NAME


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY)

    def generate(self, prompt: str, temperature: float = 0.4, max_tokens: int = 1200) -> str:
        """Send user prompt to the LLM model and return the output text."""
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except AuthenticationError:
            raise RuntimeError(
                "Invalid OpenAI API key. Check your .env file."
            )

        except RateLimitError:
            raise RuntimeError(
                "OpenAI rate limit reached. Wait a moment and try again."
            )

        except APIConnectionError:
            raise RuntimeError(
                "Could not connect to OpenAI. Check your internet connection."
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e