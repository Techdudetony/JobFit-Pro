'''
Wrapper around the OpenAI API to keep our code modular, testable, and easy to swap later.
'''
from openai import OpenAI
from services.config import API_KEY, MODEL_NAME

class OpenAIClient:
    '''Small abstraction layer over the OpenAI Chat API'''
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY)
        
    def generate(self, prompt: str) -> str:
        '''Send user prompt to the LLM model and return the output text.'''
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"]