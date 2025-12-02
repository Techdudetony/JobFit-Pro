'''
Fetch a job description from a URL or convert HTML to clean text.
'''
import requests
from bs4 import BeautifulSoup

def fetch_job_description(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception:
        return ""
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove elements that contain no job content
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.extract()
        
    text = soup.get_text(separator=" ", strip=True)
    return text