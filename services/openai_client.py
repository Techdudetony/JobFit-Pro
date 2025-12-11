"""
Wrapper around the OpenAI API to keep our code modular, testable, and easy to swap later.
"""

from openai import OpenAI
from services.config import API_KEY, MODEL_NAME


class OpenAIClient:
    """Small abstraction layer over the OpenAI Chat API"""

    def __init__(self):
        self.client = OpenAI(api_key=API_KEY)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Send user prompt to the LLM model and return the output text.

        kwargs allow optional tuning parameters such as:
        - temperature
        - max_tokens
        - frequency_penalty
        - presence_penalty
        """
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            return response.choices[0].message.content
        except Exception as e:
            print("[OpenAI Error]", e)
            return "OpenAI request failed. Please try again."
