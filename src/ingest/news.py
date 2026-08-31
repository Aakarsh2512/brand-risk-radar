"""Fetch brand mentions from NewsAPI.org."""
import hashlib
from datetime import datetime, timezone

import requests

from src.config import NEWSAPI_KEY

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def _make_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def fetch_news_mentions(brand: str, from_date: str = None, page_size: int = 100) -> list[dict]:
    """Fetch articles mentioning `brand`. from_date is an ISO date string (YYYY-MM-DD)."""
    params = {
        "q": brand,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWSAPI_KEY,
    }
    if from_date:
        params["from"] = from_date

    resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
    resp.raise_for_status()
    articles = resp.json().get("articles", [])

    now = datetime.now(timezone.utc).isoformat()
    mentions = []
    for a in articles:
        if not a.get("url") or not a.get("publishedAt"):
            continue
        mentions.append(
            {
                "id": _make_id(a["url"]),
                "brand": brand,
                "source_type": "news",
                "source_name": (a.get("source") or {}).get("name"),
                "title": a.get("title"),
                "text": a.get("description") or a.get("content") or "",
                "url": a["url"],
                "author": a.get("author"),
                "published_at": a["publishedAt"],
                "fetched_at": now,
            }
        )
    return mentions
