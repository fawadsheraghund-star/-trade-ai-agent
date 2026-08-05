import os
from openai import OpenAI
from utils.logger import logger

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def ai_summary(prompt: str):
    if not OPENAI_API_KEY:
        logger.info("OpenAI key not present, skipping AI analysis.")
        return {"summary": "", "confidence": 0.0}
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(model="gpt-4o-mini", input=prompt, max_tokens=300)
    text = resp.output_text if hasattr(resp, "output_text") else str(resp)
    return {"summary": text, "confidence": 0.6}
