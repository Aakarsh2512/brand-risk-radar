"""Entry point for the topic extraction step: cluster canonical (deduplicated)
mentions per brand into topics using BERTopic, and store the topic_id per
mention plus a keyword summary per topic. Run this after dedup.
"""
from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.topics.model import fit_topic_model

MIN_TOPIC_SIZE = 3


def run(min_topic_size: int = MIN_TOPIC_SIZE) -> None:
    conn = get_connection()
    for brand in TRACKED_BRANDS:
        rows = conn.execute(
            "SELECT id, title, text FROM mentions WHERE brand = ? AND is_canonical = 1",
            (brand,),
        ).fetchall()
        if len(rows) < min_topic_size * 2:
            print(f"[{brand}] only {len(rows)} canonical mentions, skipping (need more data)")
            continue

        ids = [r[0] for r in rows]
        texts = [f"{r[1] or ''}. {r[2] or ''}".strip() for r in rows]

        topic_model = fit_topic_model(texts, min_topic_size=min_topic_size)
        topic_ids = topic_model.topics_

        for mention_id, topic_id in zip(ids, topic_ids):
            conn.execute("UPDATE mentions SET topic_id = ? WHERE id = ?", (int(topic_id), mention_id))

        conn.execute("DELETE FROM topics WHERE brand = ?", (brand,))
        for _, row in topic_model.get_topic_info().iterrows():
            tid = int(row["Topic"])
            if tid == -1:
                keywords = "(outliers / no clear topic)"
            else:
                keywords = ", ".join(word for word, _ in topic_model.get_topic(tid)[:8])
            conn.execute(
                "INSERT INTO topics (brand, topic_id, keywords, size) VALUES (?, ?, ?, ?)",
                (brand, tid, keywords, int(row["Count"])),
            )
        conn.commit()

        n_topics = len(set(topic_ids) - {-1})
        n_outliers = list(topic_ids).count(-1)
        print(f"[{brand}] {len(rows)} mentions -> {n_topics} topics ({n_outliers} outliers)")


if __name__ == "__main__":
    run()
