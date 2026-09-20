"""Entry point for the drift detection step: build each brand's windowed topic
distribution, score narrative drift, normalize it against that brand's own
history, and flag changepoints. Run this after topic extraction.
"""
from collections import Counter, defaultdict
from datetime import datetime

from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.drift.changepoint import compute_drift_scores, detect_changepoints, normalize_drift
from src.drift.topic_distribution import build_windowed_topic_distribution

WINDOW_DAYS = 7

# A topic distribution needs a reasonable number of documents behind it before
# a shift in it means anything. Below this, a single article can flip the mix.
MIN_WINDOW_MENTIONS = 10


def _to_date(published_at: str) -> str:
    return datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()


def run(brands: list[str] | None = None, window_days: int = WINDOW_DAYS) -> None:
    conn = get_connection()
    for brand in (brands or TRACKED_BRANDS):
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

        dates, _topic_ids, distribution, window_totals = build_windowed_topic_distribution(
            rows, window_days
        )
        if not dates:
            print(f"[{brand}] no windows to score, skipping")
            continue

        # Compare each window against the previous non-overlapping one.
        raw_drift = compute_drift_scores(distribution, lag=window_days)
        reliable = [t >= MIN_WINDOW_MENTIONS for t in window_totals]
        drift_z = normalize_drift(raw_drift, reliable=reliable)
        changepoint_idx = set(detect_changepoints(distribution))

        mention_count_by_date = Counter()
        topic_counts_by_date = defaultdict(Counter)
        for published_at, topic_id in rows:
            d = _to_date(published_at)
            mention_count_by_date[d] += 1
            topic_counts_by_date[d][topic_id] += 1

        # This step recomputes every day's stats from scratch, but some columns
        # belong to other steps: `alerted` to the alert step, `mean_sentiment`
        # to the sentiment step. Dropping them here would re-fire alerts that
        # already went out and silently zero the sentiment term in the risk
        # score, so they're carried across the rebuild.
        carried = {
            d: (alerted, sentiment)
            for d, alerted, sentiment in conn.execute(
                "SELECT date, alerted, mean_sentiment FROM daily_stats WHERE brand = ?", (brand,)
            )
        }

        conn.execute("DELETE FROM daily_stats WHERE brand = ?", (brand,))
        for i, d in enumerate(dates):
            dominant = topic_counts_by_date[d].most_common(1)
            conn.execute(
                """
                INSERT INTO daily_stats
                    (brand, date, mention_count, window_mentions, dominant_topic,
                     drift_score, drift_z, is_changepoint, alerted, mean_sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brand,
                    d,
                    mention_count_by_date.get(d, 0),
                    window_totals[i],
                    dominant[0][0] if dominant else None,
                    raw_drift[i],
                    drift_z[i],
                    1 if i in changepoint_idx else 0,
                    carried.get(d, (0, None))[0] or 0,
                    carried.get(d, (0, None))[1],
                ),
            )
        conn.commit()

        peak = max(drift_z) if drift_z else 0.0
        thin = sum(1 for r in reliable if not r)
        thin_note = f", {thin} windows too thin to score" if thin else ""
        print(
            f"[{brand}] {len(dates)} windows, raw drift mean={sum(raw_drift)/len(raw_drift):.2f}, "
            f"peak z={peak:+.1f}, {len(changepoint_idx)} changepoints{thin_note}"
        )


if __name__ == "__main__":
    run()
