"""Entry point for the drift detection step: build each brand's daily topic
distribution, score narrative drift day-over-day, and flag changepoints
where enough history exists. Run this after topic extraction.
"""
from collections import Counter, defaultdict
from datetime import datetime

from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.drift.changepoint import compute_drift_scores, detect_changepoints
from src.drift.topic_distribution import build_daily_topic_distribution


def _to_date(published_at: str) -> str:
    return datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()


def run() -> None:
    conn = get_connection()
    for brand in TRACKED_BRANDS:
        rows = conn.execute(
            """
            SELECT published_at, topic_id FROM mentions
            WHERE brand = ? AND is_canonical = 1 AND topic_id IS NOT NULL
            """,
            (brand,),
        ).fetchall()
        if not rows:
            print(f"[{brand}] no topic-tagged mentions yet, skipping")
            continue

        dates, topic_ids, distribution = build_daily_topic_distribution(rows)
        drift_scores = compute_drift_scores(distribution)
        changepoint_idx = set(detect_changepoints(distribution))

        # dominant topic per day = topic with the highest share that day
        dominant_topic_by_date = {}
        mention_count_by_date = Counter()
        topic_counts_by_date = defaultdict(Counter)
        for published_at, topic_id in rows:
            date = _to_date(published_at)
            mention_count_by_date[date] += 1
            topic_counts_by_date[date][topic_id] += 1
        for date in dates:
            dominant_topic_by_date[date] = topic_counts_by_date[date].most_common(1)[0][0]

        conn.execute("DELETE FROM daily_stats WHERE brand = ?", (brand,))
        for i, date in enumerate(dates):
            conn.execute(
                """
                INSERT INTO daily_stats (brand, date, mention_count, dominant_topic, drift_score, is_changepoint)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    brand,
                    date,
                    mention_count_by_date[date],
                    dominant_topic_by_date[date],
                    drift_scores[i],
                    1 if i in changepoint_idx else 0,
                ),
            )
        conn.commit()

        n_days = len(dates)
        pelt_note = "" if n_days >= 8 else f" (changepoint detection needs >= 8 days of history, only have {n_days})"
        print(f"[{brand}] {n_days} days of history, max drift_score={max(drift_scores):.2f}, "
              f"{len(changepoint_idx)} changepoints flagged{pelt_note}")


if __name__ == "__main__":
    run()
