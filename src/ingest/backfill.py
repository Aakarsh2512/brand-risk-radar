"""Backfill historical mentions for every tracked brand.

NewsAPI's free tier serves roughly the last month and caps each response at
100 articles. With `qInTitle` the per-brand volume is only a few articles a
day, so a week-wide window fits comfortably inside one request -- meaning a
month of history costs ~5 requests per brand instead of one per day.

This is what makes the project evaluable now rather than in three weeks: the
history arrives up front, across every brand at once.

Usage:  python -m src.ingest.backfill [days_back]
"""
import sys
from datetime import date, timedelta

from src.config import TRACKED_BRANDS
from src.db import get_connection, upsert_mentions
from src.ingest.news import fetch_news_mentions

WINDOW_DAYS = 7
DEFAULT_DAYS_BACK = 30
PAGE_SIZE = 100

# NewsAPI's free tier allows 100 requests/day, so a backfill has to stay inside
# a budget or it starts silently failing partway through.
DEFAULT_BUDGET = 90


class Budget:
    def __init__(self, limit: int):
        self.limit, self.used = limit, 0

    def spend(self) -> bool:
        if self.used >= self.limit:
            return False
        self.used += 1
        return True


def _fetch_window(conn, brand: str, start: date, end: date, budget: Budget, depth: int = 0) -> int:
    """Fetch one window, splitting it if the response came back truncated.

    A response at exactly PAGE_SIZE means NewsAPI capped it and we're only
    seeing the newest slice of the window -- for a high-volume brand a whole
    week can collapse into a single day of coverage, which quietly destroys the
    time series. Halving the window until it fits is what keeps daily coverage
    honest.
    """
    if not budget.spend():
        return 0
    try:
        mentions, total_results = fetch_news_mentions(
            brand,
            from_date=start.isoformat(),
            to_date=end.isoformat(),
            page_size=PAGE_SIZE,
            with_meta=True,
        )
    except Exception as e:  # noqa: BLE001 -- one bad window shouldn't kill the backfill
        print(f"  [{brand}] {start}..{end} failed: {e}")
        return 0

    # `total_results` is what NewsAPI matched, before our relevance filter --
    # comparing the filtered list to the cap would under-report truncation.
    truncated = total_results > PAGE_SIZE
    span = (end - start).days

    if truncated and span >= 1 and budget.used < budget.limit:
        mid = start + timedelta(days=span // 2)
        return (
            _fetch_window(conn, brand, start, mid, budget, depth + 1)
            + _fetch_window(conn, brand, mid + timedelta(days=1), end, budget, depth + 1)
        )

    inserted = upsert_mentions(conn, mentions) if mentions else 0
    warn = f"  <- capped: {total_results} matched in 1 day, sampled 100" if truncated and span == 0 else ""
    print(f"  [{brand}] {start}..{end}: {len(mentions)} relevant, {inserted} new{warn}")
    return inserted


def run(
    days_back: int = DEFAULT_DAYS_BACK,
    brands: list[str] | None = None,
    budget: int = DEFAULT_BUDGET,
) -> None:
    conn = get_connection()
    today = date.today()
    bud = Budget(budget)

    for brand in (brands or TRACKED_BRANDS):
        brand_total = 0
        window_start = today - timedelta(days=days_back)

        while window_start <= today and bud.used < bud.limit:
            window_end = min(window_start + timedelta(days=WINDOW_DAYS - 1), today)
            brand_total += _fetch_window(conn, brand, window_start, window_end, bud)
            window_start = window_end + timedelta(days=1)

        print(f"[{brand}] {brand_total} new mentions stored\n")

    print(f"done -- {bud.used}/{bud.limit} API requests used")


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DAYS_BACK
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BUDGET
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    run(days, brands=only, budget=budget)
