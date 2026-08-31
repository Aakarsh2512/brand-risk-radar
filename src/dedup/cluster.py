"""Greedy near-duplicate clustering by cosine similarity.

Mentions are processed in order; each is compared against the representative
(first item) of every cluster seen so far. If it's similar enough to an
existing cluster, it joins that cluster; otherwise it starts a new one.

This is O(n * k) where k is the number of clusters -- fine at the scale of a
few hundred mentions per brand per run. A full pairwise approach (HDBSCAN on
the similarity matrix) would be more principled at larger scale, but for
detecting "5 outlets reported the same wire story today" this is simple,
fast, and easy to explain.
"""
import numpy as np


def cluster_by_similarity(embeddings: np.ndarray, threshold: float = 0.82) -> list[int]:
    n = len(embeddings)
    cluster_ids = [-1] * n
    representatives: list[tuple[int, np.ndarray]] = []

    for i in range(n):
        best_cluster = None
        for cid, rep_emb in representatives:
            sim = float(np.dot(embeddings[i], rep_emb))
            if sim >= threshold:
                best_cluster = cid
                break
        if best_cluster is None:
            best_cluster = len(representatives)
            representatives.append((best_cluster, embeddings[i]))
        cluster_ids[i] = best_cluster

    return cluster_ids
