"""Entry point for the ingestion step: pull mentions for every tracked brand
and store new ones in SQLite. Run this on a schedule (see README).
"""
import requests

from src.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, TRACKED_BRANDS
from src.db import get_connection, upsert_mentions
from src.ingest.news import fetch_news_mentions
from src.ingest.reddit import fetch_reddit_mentions

REDDIT_CONFIGURED = bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)


def run(brands: list[str] | None = None) -> None:
    conn = get_connection()
    failures = []

    for brand in (brands or TRACKED_BRANDS):
        # A failure on one brand must not take the run down with it. NewsAPI's
        # free tier allows 100 requests/24h, and once that's spent every
        # remaining brand returns 429 -- letting that propagate meant a single
        # exhausted quota skipped the other brands *and* every downstream stage
        # (dedup, topics, drift, sentiment, risk), so a whole day produced
        # nothing at all.
        try:
            news = fetch_news_mentions(brand)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            reason = "rate limit reached" if status == 429 else f"HTTP {status}"
            print(f"[{brand}] news fetch failed ({reason}), skipping")
            failures.append(brand)
            continue
        except requests.RequestException as e:
            print(f"[{brand}] news fetch failed ({type(e).__name__}), skipping")
            failures.append(brand)
            continue

        try:
            reddit = fetch_reddit_mentions(brand) if REDDIT_CONFIGURED else []
        except Exception as e:  # noqa: BLE001 -- Reddit is a bonus source, never fatal
            print(f"[{brand}] reddit fetch failed ({type(e).__name__}), continuing with news only")
            reddit = []

        inserted = upsert_mentions(conn, news + reddit)
        print(f"[{brand}] fetched {len(news)} news + {len(reddit)} reddit, "
              f"{inserted} new rows stored")

    if not REDDIT_CONFIGURED:
        print("  (Reddit skipped: REDDIT_CLIENT_ID/SECRET not set in .env)")
    if failures:
        print(f"  ({len(failures)} brand(s) skipped this run: {', '.join(failures)})")


if __name__ == "__main__":
    run()
