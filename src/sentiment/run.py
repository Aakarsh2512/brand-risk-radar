"""Entry point for the sentiment step: classify canonical mentions with a
pretrained transformer and store per-mention + daily-aggregate sentiment.
Only canonical (deduplicated) mentions are scored, to avoid wasting compute
re-classifying the same wire story five times.
"""
from collections import defaultdict
from datetime import datetime

from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.sentiment.model import classify


def _to_date(published_at: str) -> str:
    return datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()


def run(brands: list[str] | None = None) -> None:
    conn = get_connection()
    for brand in (brands or TRACKED_BRANDS):
        rows = conn.execute(
            "SELECT id, title, text, published_at FROM mentions WHERE brand = ? AND is_canonical = 1",
            (brand,),
        ).fetchall()
        if not rows:
            print(f"[{brand}] no canonical mentions yet, skipping")
            continue

        ids = [r[0] for r in rows]
        texts = [f"{r[1] or ''}. {r[2] or ''}".strip()[:512] for r in rows]
        published = [r[3] for r in rows]

        results = classify(texts)

        scores_by_date = defaultdict(list)
        for mention_id, (label, score), pub in zip(ids, results, published):
            conn.execute(
                "UPDATE mentions SET sentiment_label = ?, sentiment_score = ? WHERE id = ?",
                (label, score, mention_id),
            )
            scores_by_date[_to_date(pub)].append(score)
        conn.commit()

        # Upsert into daily_stats: a row may already exist (from the drift
        # step) or not, depending on run order -- either way we just want
        # mean_sentiment set correctly for that brand/date.
        for date, scores in scores_by_date.items():
            mean_sentiment = sum(scores) / len(scores)
            conn.execute(
                """
                INSERT INTO daily_stats (brand, date, mean_sentiment)
                VALUES (?, ?, ?)
                ON CONFLICT(brand, date) DO UPDATE SET mean_sentiment = excluded.mean_sentiment
                """,
                (brand, date, mean_sentiment),
            )
        conn.commit()

        overall_mean = sum(s for _, s in results) / len(results)
        print(f"[{brand}] classified {len(rows)} mentions, mean sentiment {overall_mean:+.2f}")


if __name__ == "__main__":
    run()
