"""Fetch brand mentions from Reddit via PRAW (search across all of Reddit)."""
import hashlib
from datetime import datetime, timezone

import praw

from src.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT


def _make_id(reddit_id: str) -> str:
    return hashlib.sha256(reddit_id.encode()).hexdigest()[:16]


def _client() -> praw.Reddit:
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def fetch_reddit_mentions(brand: str, limit: int = 100) -> list[dict]:
    reddit = _client()
    now = datetime.now(timezone.utc).isoformat()

    mentions = []
    for submission in reddit.subreddit("all").search(brand, sort="new", limit=limit):
        published_at = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat()
        mentions.append(
            {
                "id": _make_id(submission.id),
                "brand": brand,
                "source_type": "reddit",
                "source_name": str(submission.subreddit),
                "title": submission.title,
                "text": submission.selftext or "",
                "url": f"https://reddit.com{submission.permalink}",
                "author": str(submission.author) if submission.author else None,
                "published_at": published_at,
                "fetched_at": now,
            }
        )
    return mentions
