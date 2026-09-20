"""Builds topic-distribution time series from per-mention topic assignments.

Two shapes are supported:

* daily -- what fraction of *today's* mentions fell into each topic
* windowed -- what fraction of the *trailing N days'* mentions did

The windowed form is what the pipeline actually uses. At realistic volumes a
single brand-day is only a handful of relevant articles, so a day-over-day
comparison mostly measures which stories happened to publish that morning, not
whether the narrative moved. Comparing a 7-day window against the previous
7-day window smooths that out and matches how a comms team actually thinks
about it ("what changed this week").
"""
from collections import defaultdict
from datetime import date, datetime, timedelta


def _to_date(published_at: str) -> str:
    return datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()


def _counts_by_date(rows: list[tuple[str, int]]) -> dict[str, dict[int, int]]:
    counts: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for published_at, topic_id in rows:
        counts[_to_date(published_at)][topic_id] += 1
    return counts


def build_daily_topic_distribution(
    rows: list[tuple[str, int]],
) -> tuple[list[str], list[int], list[list[float]]]:
    """rows: list of (published_at, topic_id).

    Returns (dates, topic_ids, distribution) where distribution[i][j] is the
    fraction of mentions on dates[i] belonging to topic_ids[j].
    """
    counts_by_date = _counts_by_date(rows)
    dates = sorted(counts_by_date)
    topic_ids = sorted({t for c in counts_by_date.values() for t in c})

    distribution = []
    for d in dates:
        day = counts_by_date[d]
        total = sum(day.values())
        distribution.append([day.get(t, 0) / total for t in topic_ids])

    return dates, topic_ids, distribution


def build_windowed_topic_distribution(
    rows: list[tuple[str, int]], window_days: int = 7
) -> tuple[list[str], list[int], list[list[float]], list[int]]:
    """Same, but each entry covers the trailing `window_days` ending that day.

    Dates run continuously from the first to the last observed day, including
    days with no coverage of their own -- a quiet day still has a window around
    it, and skipping it would silently compress the time axis.

    Windows only start once a full `window_days` of history exists. A partial
    leading window covers less time than the ones it's later compared against,
    and that mismatch alone registers as a large false drift at the start of
    every brand's series.

    Also returns each window's total mention count, so callers can discount
    windows too thin to carry a distribution at all.
    """
    counts_by_date = _counts_by_date(rows)
    if not counts_by_date:
        return [], [], [], []

    observed = sorted(counts_by_date)
    topic_ids = sorted({t for c in counts_by_date.values() for t in c})
    first = date.fromisoformat(observed[0])
    last = date.fromisoformat(observed[-1])

    dates, distribution, window_totals = [], [], []
    cursor = first + timedelta(days=window_days - 1)
    while cursor <= last:
        window_total: dict[int, int] = defaultdict(int)
        for offset in range(window_days):
            day = (cursor - timedelta(days=offset)).isoformat()
            for topic_id, n in counts_by_date.get(day, {}).items():
                window_total[topic_id] += n

        total = sum(window_total.values())
        if total:
            dates.append(cursor.isoformat())
            distribution.append([window_total.get(t, 0) / total for t in topic_ids])
            window_totals.append(total)
        cursor += timedelta(days=1)

    return dates, topic_ids, distribution, window_totals
