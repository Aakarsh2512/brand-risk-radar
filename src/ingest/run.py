"""Entry point for the ingestion step: pull mentions for every tracked brand
and store new ones in SQLite. Run this on a schedule (see README).
"""
from src.config import TRACKED_BRANDS
from src.db import get_connection, upsert_mentions
from src.ingest.news import fetch_news_mentions
from src.ingest.reddit import fetch_reddit_mentions


def run() -> None:
    conn = get_connection()
    for brand in TRACKED_BRANDS:
        news = fetch_news_mentions(brand)
        reddit = fetch_reddit_mentions(brand)

        inserted = upsert_mentions(conn, news + reddit)
        print(f"[{brand}] fetched {len(news)} news + {len(reddit)} reddit, "
              f"{inserted} new rows stored")


if __name__ == "__main__":
    run()
