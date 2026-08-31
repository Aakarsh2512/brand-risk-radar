"""Entry point for the dedup step: cluster near-duplicate mentions per brand
using sentence embeddings + cosine similarity, and mark one canonical mention
per cluster (the earliest-published one). Run this after ingestion.
"""
import uuid

from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.dedup.cluster import cluster_by_similarity
from src.dedup.embed import embed_texts

SIMILARITY_THRESHOLD = 0.82


def run(threshold: float = SIMILARITY_THRESHOLD, brands: list[str] | None = None) -> None:
    conn = get_connection()
    for brand in (brands or TRACKED_BRANDS):
        rows = conn.execute(
            "SELECT id, title, text, published_at FROM mentions WHERE brand = ? ORDER BY published_at",
            (brand,),
        ).fetchall()
        if not rows:
            continue

        ids = [r[0] for r in rows]
        texts = [f"{r[1] or ''}. {r[2] or ''}".strip() for r in rows]
        published = [r[3] for r in rows]

        embeddings = embed_texts(texts)
        cluster_ids = cluster_by_similarity(embeddings, threshold)

        # Earliest-published mention in each cluster is the canonical one.
        canonical_for_cluster = {}
        for mention_id, cid, pub in zip(ids, cluster_ids, published):
            if cid not in canonical_for_cluster or pub < canonical_for_cluster[cid][1]:
                canonical_for_cluster[cid] = (mention_id, pub)

        group_uuid_for_cluster = {cid: uuid.uuid4().hex[:12] for cid in set(cluster_ids)}

        for mention_id, cid in zip(ids, cluster_ids):
            is_canonical = 1 if canonical_for_cluster[cid][0] == mention_id else 0
            conn.execute(
                "UPDATE mentions SET dedup_group_id = ?, is_canonical = ? WHERE id = ?",
                (group_uuid_for_cluster[cid], is_canonical, mention_id),
            )
        conn.commit()

        n_clusters = len(set(cluster_ids))
        print(
            f"[{brand}] {len(rows)} mentions -> {n_clusters} unique stories "
            f"({len(rows) - n_clusters} duplicates merged)"
        )


if __name__ == "__main__":
    run()
