"""Builds a daily topic-distribution time series from per-mention topic
assignments: for each day, what fraction of that day's mentions fell into
each topic. This is the input to drift/changepoint detection.
"""
from collections import defaultdict
from datetime import datetime


def _to_date(published_at: str) -> str:
    return datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()


def build_daily_topic_distribution(rows: list[tuple[str, int]]) -> tuple[list[str], list[int], list[list[float]]]:
    """rows: list of (published_at, topic_id).

    Returns (dates, topic_ids, distribution) where distribution[i][j] is the
    fraction of mentions on dates[i] that belong to topic_ids[j]. dates are
    sorted ascending; topic_ids includes -1 (outliers) if present.
    """
    counts_by_date: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for published_at, topic_id in rows:
        date = _to_date(published_at)
        counts_by_date[date][topic_id] += 1

    dates = sorted(counts_by_date.keys())
    topic_ids = sorted({tid for counts in counts_by_date.values() for tid in counts})

    distribution = []
    for date in dates:
        day_counts = counts_by_date[date]
        total = sum(day_counts.values())
        distribution.append([day_counts.get(tid, 0) / total for tid in topic_ids])

    return dates, topic_ids, distribution
