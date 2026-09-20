"""BERTopic wrapper tuned for small, single-brand mention corpora.

BERTopic composes: sentence embeddings -> UMAP (dimensionality reduction)
-> HDBSCAN (density-based clustering) -> c-TF-IDF (per-cluster keyword
extraction). We reuse the same embedding model as the dedup step so a
mention's vector representation is consistent across the pipeline.

min_topic_size is set much lower than BERTopic's default (10) because we're
working with a few dozen to a few hundred mentions per brand, not the huge
news corpora BERTopic's defaults assume.

REPRODUCIBILITY
---------------
UMAP initializes randomly by default, so refitting on identical data produced
a different set of topics every run -- and because drift is measured over the
topic distribution, the *entire history* of drift scores changed with it. Two
runs over the same corpus disagreed on whether a day was a +7.6 sigma spike or
a +2.9 one, and on how many topics existed at all.

Pinning `random_state` makes the pipeline deterministic, which matters here
more than usual: the daily job recomputes history from scratch, so without it
yesterday's reported numbers silently stop matching today's. The cost is that
UMAP falls back to single-threaded execution.
"""
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from src.dedup.embed import get_model as get_embedding_model

RANDOM_STATE = 42


def fit_topic_model(texts: list[str], min_topic_size: int = 3) -> BERTopic:
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    # Mirrors BERTopic's own UMAP defaults, with the seed pinned.
    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=RANDOM_STATE,
    )
    topic_model = BERTopic(
        embedding_model=get_embedding_model(),
        umap_model=umap_model,
        vectorizer_model=vectorizer,
        min_topic_size=min_topic_size,
        calculate_probabilities=False,
        verbose=False,
    )
    topic_model.fit(texts)
    return topic_model
