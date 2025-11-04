import os
import requests
from typing import List, Dict, Any

from django.conf import settings

NEWS_API_KEY = getattr(settings, "NEWS_API_KEY", "")
HF_API_KEY = getattr(settings, "HF_API_KEY", "")

# NewsAPI endpoint (free tier)
NEWS_API_URL = "https://newsapi.org/v2/everything"

def fetch_engineering_news(query: str = "engineering", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent engineering-related news via NewsAPI.
    Returns a list of article dicts with keys: title, description, url, publishedAt
    """
    if not NEWS_API_KEY:
        print("NEWS_API_KEY not set")
        return []

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": NEWS_API_KEY,
    }
    try:
        r = requests.get(NEWS_API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", []) or []
        # Normalize minimal fields
        results = []
        for a in articles:
            results.append({
                "title": a.get("title"),
                "description": a.get("description") or a.get("content") or "",
                "url": a.get("url"),
                "publishedAt": a.get("publishedAt"),
            })
        return results
    except Exception as e:
        print("Error fetching news:", e)
        return []

def summarize_with_hf(text: str) -> str:
    """
    Summarize given text using Hugging Face Inference API (facebook/bart-large-cnn).
    If HF token missing or API fails, falls back to a truncated excerpt.
    """
    if not HF_API_KEY:
        # fallback: short truncation
        return text[:300] + ("..." if len(text) > 300 else "")

    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text}
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # The inference API returns a list with 'summary_text' or a list of dicts
        if isinstance(data, list) and len(data) > 0:
            # format can be [{'summary_text': "..." }] or [{'generated_text': "..."}]
            first = data[0]
            if isinstance(first, dict):
                return first.get("summary_text") or first.get("generated_text") or str(first)
            # or string
            return str(first)
        # Sometimes API returns dict with error or needs more processing
        if isinstance(data, dict) and "error" in data:
            print("HF error:", data["error"])
            return text[:300] + ("..." if len(text) > 300 else "")
        # fallback to raw string
        return str(data)
    except Exception as e:
        print("Error calling HF API:", e)
        return text[:300] + ("..." if len(text) > 300 else "")
