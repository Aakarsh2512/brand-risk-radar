"""BERTopic wrapper tuned for small, single-brand mention corpora.

BERTopic composes: sentence embeddings -> UMAP (dimensionality reduction)
-> HDBSCAN (density-based clustering) -> c-TF-IDF (per-cluster keyword
extraction). We reuse the same embedding model as the dedup step so a
mention's vector representation is consistent across the pipeline.

min_topic_size is set much lower than BERTopic's default (10) because we're
working with a few dozen to a few hundred mentions per brand, not the huge
news corpora BERTopic's defaults assume.
"""
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

from src.dedup.embed import get_model as get_embedding_model


def fit_topic_model(texts: list[str], min_topic_size: int = 3) -> BERTopic:
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    topic_model = BERTopic(
        embedding_model=get_embedding_model(),
        vectorizer_model=vectorizer,
        min_topic_size=min_topic_size,
        calculate_probabilities=False,
        verbose=False,
    )
    topic_model.fit(texts)
    return topic_model
