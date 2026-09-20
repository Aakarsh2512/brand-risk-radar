"""Fetch brand mentions from NewsAPI.org.

Relevance is enforced with `qInTitle` rather than `q`. The original loose
full-text query matched any article where the brand appeared anywhere in the
body, which produced a corpus that was ~79% irrelevant (a metal band's tour,
exam rankings, a temple ceremony -- all "about Boeing"). That noise made the
daily topic mix churn at random, which saturated the drift signal and left the
changepoint detector unable to fire at all. Filtering at the source is the fix.
"""
import hashlib
from datetime import datetime, timezone

import requests

from src.config import NEWSAPI_KEY, RELEVANCE_REQUIRES_BRAND_IN_TITLE

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def _make_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def is_relevant(brand: str, title: str | None, text: str | None) -> bool:
    """A mention counts only if the brand is named in the headline.

    `qInTitle` already enforces this server-side; this is a second line of
    defence, and it's also what the one-off purge of legacy rows uses.
    """
    if not RELEVANCE_REQUIRES_BRAND_IN_TITLE:
        return bool(brand.lower() in f"{title or ''} {text or ''}".lower())
    return brand.lower() in (title or "").lower()


def fetch_news_mentions(
    brand: str,
    from_date: str | None = None,
    to_date: str | None = None,
    page_size: int = 100,
    with_meta: bool = False,
):
    """Fetch articles with `brand` in the headline.

    from_date/to_date are ISO date strings (YYYY-MM-DD). NewsAPI's free tier
    serves roughly the last month, so windowed queries let us backfill history
    immediately instead of waiting for it to accumulate day by day.

    With `with_meta`, also returns NewsAPI's `totalResults` for the window.
    That's the reliable way to detect a capped response: the returned list is
    post-filtered, so counting it under-reports truncation.
    """
    params = {
        "qInTitle": brand,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWSAPI_KEY,
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    resp = requests.get(NEWSAPI_URL, params=params, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    articles = payload.get("articles", [])
    total_results = payload.get("totalResults", len(articles))

    now = datetime.now(timezone.utc).isoformat()
    mentions = []
    for a in articles:
        if not a.get("url") or not a.get("publishedAt"):
            continue
        title = a.get("title")
        text = a.get("description") or a.get("content") or ""
        if not is_relevant(brand, title, text):
            continue
        mentions.append(
            {
                "id": _make_id(a["url"]),
                "brand": brand,
                "source_type": "news",
                "source_name": (a.get("source") or {}).get("name"),
                "title": title,
                "text": text,
                "url": a["url"],
                "author": a.get("author"),
                "published_at": a["publishedAt"],
                "fetched_at": now,
            }
        )
    return (mentions, total_results) if with_meta else mentions
