from openai import OpenAI
from services.config import API_KEY, MODEL_NAME


class OpenAIClient:
    def __init__(self):
        # Initialize client with your API key
        self.client = OpenAI(api_key=API_KEY)

    def generate(self, prompt: str, temperature=0.4, max_tokens=1200):
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            print("[OpenAI Error]", e)
            return ""
