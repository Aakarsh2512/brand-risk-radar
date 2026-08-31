"""Sentence embedding wrapper. Model loads once and is reused across calls."""
from sentence_transformers import SentenceTransformer

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # Small, fast, CPU-friendly model -- good enough for near-duplicate
        # detection; no need for a larger model here.
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: list[str]):
    """Returns L2-normalized embeddings, so cosine similarity == dot product."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
