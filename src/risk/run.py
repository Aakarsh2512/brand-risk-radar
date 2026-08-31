"""Entry point for the composite risk-score step: reads each brand's
daily_stats (populated by the drift and sentiment steps) and computes a
risk score + band per day. Run this last, after drift and sentiment.
"""
from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.risk.score import BASELINE_WINDOW, score_day


def run() -> None:
    conn = get_connection()
    for brand in TRACKED_BRANDS:
        rows = conn.execute(
            """
            SELECT date, mention_count, drift_score, is_changepoint, mean_sentiment
            FROM daily_stats WHERE brand = ? ORDER BY date
            """,
            (brand,),
        ).fetchall()
        if not rows:
            print(f"[{brand}] no daily_stats yet, skipping")
            continue

        for i, (date, count, drift, is_cp, sentiment) in enumerate(rows):
            window = rows[max(0, i - BASELINE_WINDOW):i]
            baseline_counts = [r[1] for r in window if r[1] is not None]
            baseline_sentiments = [r[4] for r in window if r[4] is not None]

            result = score_day(
                drift_score=drift or 0.0,
                is_changepoint=bool(is_cp),
                today_count=count or 0,
                baseline_counts=baseline_counts,
                today_sentiment=sentiment or 0.0,
                baseline_sentiments=baseline_sentiments,
            )
            conn.execute(
                "UPDATE daily_stats SET risk_score = ?, risk_band = ? WHERE brand = ? AND date = ?",
                (result["score"], result["band"], brand, date),
            )
        conn.commit()

        latest_date = rows[-1][0]
        latest = conn.execute(
            "SELECT risk_score, risk_band FROM daily_stats WHERE brand = ? AND date = ?",
            (brand, latest_date),
        ).fetchone()
        print(f"[{brand}] latest ({latest_date}): risk_score={latest[0]:.1f} band={latest[1]}")


if __name__ == "__main__":
    run()
