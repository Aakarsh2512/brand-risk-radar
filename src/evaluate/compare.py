"""Head-to-head comparison of the three signals.

The project's premise is that a narrative pivot is a better early warning than
sentiment or volume alone. That's a claim, and a claim needs a test: this runs
each signal as its own independent detector over the same brand-days and
reports what each one catches, what it misses, and where they disagree.

Each detector fires on a z-score threshold against the brand's own history, so
all three are on the same footing -- no detector gets an unfair advantage from
being measured on a different scale.

Usage:  python -m src.evaluate.compare
"""
import statistics
from collections import defaultdict

from src.config import TRACKED_BRANDS
from src.db import get_connection

Z_THRESHOLD = 2.0
MIN_BASELINE = 5


def _trailing_z(series: list[float | None], i: int, invert: bool = False) -> float:
    """Z-score of point i against the points before it. `invert` scores drops
    rather than rises (sentiment getting worse is a fall, not a spike).
    """
    baseline = [v for v in series[:i] if v is not None]
    if len(baseline) < MIN_BASELINE or series[i] is None:
        return 0.0
    mean = statistics.mean(baseline)
    std = statistics.pstdev(baseline)
    if std < 1e-9:
        return 0.0
    z = (series[i] - mean) / std
    return -z if invert else z


def run() -> None:
    conn = get_connection()
    fired = defaultdict(set)      # detector -> {(brand, date)}
    detail = {}                   # (brand, date) -> dict of z-scores

    for brand in TRACKED_BRANDS:
        rows = conn.execute(
            """SELECT date, drift_z, mention_count, mean_sentiment
               FROM daily_stats WHERE brand = ? ORDER BY date""",
            (brand,),
        ).fetchall()
        if not rows:
            continue

        dates = [r[0] for r in rows]
        drift = [r[1] for r in rows]
        volume = [float(r[2]) if r[2] is not None else None for r in rows]
        sentiment = [r[3] for r in rows]

        for i, date in enumerate(dates):
            z_drift = drift[i] or 0.0
            z_volume = _trailing_z(volume, i)
            z_sentiment = _trailing_z(sentiment, i, invert=True)

            key = (brand, date)
            detail[key] = {"drift": z_drift, "volume": z_volume, "sentiment": z_sentiment}
            if z_drift >= Z_THRESHOLD:
                fired["drift"].add(key)
            if z_volume >= Z_THRESHOLD:
                fired["volume"].add(key)
            if z_sentiment >= Z_THRESHOLD:
                fired["sentiment"].add(key)

    total_days = len(detail)
    print(f"Compared {total_days} brand-days across {len(TRACKED_BRANDS)} brands")
    print(f"Detector fires at z >= {Z_THRESHOLD} against each brand's own history\n")

    print(f"{'detector':<12}{'fired':>7}{'rate':>8}")
    for name in ("drift", "volume", "sentiment"):
        n = len(fired[name])
        print(f"{name:<12}{n:>7}{n/total_days:>8.1%}")

    union = fired["drift"] | fired["volume"] | fired["sentiment"]
    print(f"\nDays flagged by at least one detector: {len(union)}")

    only_drift = fired["drift"] - fired["volume"] - fired["sentiment"]
    only_sent = fired["sentiment"] - fired["drift"] - fired["volume"]
    both_ds = fired["drift"] & fired["sentiment"]
    print(f"  caught by drift alone (missed by volume+sentiment): {len(only_drift)}")
    print(f"  caught by sentiment alone:                          {len(only_sent)}")
    print(f"  caught by both drift and sentiment:                 {len(both_ds)}")

    if only_drift:
        print("\n--- Days only the drift signal caught ---")
        for brand, date in sorted(only_drift):
            d = detail[(brand, date)]
            print(f"  {brand:<11}{date}   drift z={d['drift']:+.1f}  "
                  f"(volume z={d['volume']:+.1f}, sentiment z={d['sentiment']:+.1f})")
            for (t,) in conn.execute(
                """SELECT title FROM mentions WHERE brand=? AND is_canonical=1
                   AND date(published_at) BETWEEN date(?, '-6 days') AND date(?)
                   ORDER BY published_at DESC LIMIT 3""", (brand, date, date)):
                print(f"       - {t[:92]}")

    if only_sent:
        print("\n--- Days only the sentiment signal caught ---")
        for brand, date in sorted(only_sent):
            d = detail[(brand, date)]
            print(f"  {brand:<11}{date}   sentiment z={d['sentiment']:+.1f}  (drift z={d['drift']:+.1f})")


if __name__ == "__main__":
    run()
