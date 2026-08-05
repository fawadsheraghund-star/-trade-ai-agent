import os
import httpx
from transformers import pipeline
from utils.logger import logger

sentiment_pipeline = pipeline("sentiment-analysis")

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

async def fetch_news(query, pages=1):
    if not NEWSAPI_KEY:
        logger.info("No NEWSAPI_KEY provided; skipping news fetch.")
        return []
    url = "https://newsapi.org/v2/everything"
    results = []
    async with httpx.AsyncClient() as client:
        for page in range(1, pages+1):
            params = {"q": query, "apiKey": NEWSAPI_KEY, "pageSize": 20, "page": page, "language": "en"}
            r = await client.get(url, params=params, timeout=20)
            if r.status_code == 200:
                data = r.json()
                for art in data.get("articles", []):
                    results.append({"title":art.get("title"), "desc":art.get("description")})
    return results

def analyze_texts(texts):
    combined = " ".join([t.get("title","") + " " + (t.get("desc") or "") for t in texts])
    if not combined.strip():
        return {"score": 0.0, "label": "neutral"}
    out = sentiment_pipeline(combined[:4000])[0]
    return out
