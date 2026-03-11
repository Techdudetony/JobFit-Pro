<<<<<<< HEAD
"""
Wrapper around the OpenAI API to keep our code modular, testable, and easy to swap later.
"""

from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
=======
from openai import OpenAI
>>>>>>> de3b892959d22a9ace277e0b716d2ffd3b568763
from services.config import API_KEY, MODEL_NAME


class OpenAIClient:
    def __init__(self):
        # Initialize client with your API key
        self.client = OpenAI(api_key=API_KEY)

<<<<<<< HEAD
    def generate(self, prompt: str) -> str:
        """Send user prompt to the LLM model and return the output text."""
=======
    def generate(self, prompt: str, temperature=0.4, max_tokens=1200):
>>>>>>> de3b892959d22a9ace277e0b716d2ffd3b568763
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
<<<<<<< HEAD
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
=======
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            print("[OpenAI Error]", e)
            return ""
>>>>>>> de3b892959d22a9ace277e0b716d2ffd3b568763
