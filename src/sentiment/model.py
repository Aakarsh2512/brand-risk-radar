"""Sentiment classification via a pretrained transformer.

This is a *supporting* signal in the risk score, not the primary driver --
see src/drift/ for the narrative-shift detector that carries more weight.
Sentiment can stay flat while the story a brand is caught up in keeps
getting worse, which is exactly the case this project is built around.
"""
from transformers import pipeline

_classifier = None

LABEL_TO_POLARITY = {"negative": -1.0, "neutral": 0.0, "positive": 1.0}


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            truncation=True,
        )
    return _classifier


def classify(texts: list[str]) -> list[tuple[str, float]]:
    """Returns (label, signed_score) per text. signed_score is in [-1, 1]:
    the label's polarity scaled by the model's confidence, so a confident
    negative call and a wishy-washy one don't count equally.
    """
    classifier = get_classifier()
    results = classifier(texts, batch_size=16)
    output = []
    for r in results:
        label = r["label"].lower()
        polarity = LABEL_TO_POLARITY.get(label, 0.0)
        output.append((label, polarity * r["score"]))
    return output
