import requests

from src.ingest import run as ingest_run
from src.ingest.news import is_relevant


def test_relevance_requires_brand_in_headline():
    assert is_relevant("Boeing", "Boeing halts 737 deliveries", "")
    assert is_relevant("Boeing", "BOEING shares slide", "")
    # The failure mode that made 86% of the original corpus junk: brand
    # mentioned only in passing in the body.
    assert not is_relevant("Boeing", "Trivium announce world tour", "supported by Boeing")
    assert not is_relevant("Boeing", "UPSC 2026 rankings released", "")


def test_rate_limited_brand_does_not_abort_the_whole_run(monkeypatch, capsys):
    """Regression test: a 429 on one brand used to propagate and kill the run,
    so the remaining brands and every downstream stage were skipped.
    """
    calls = []

    def fake_fetch(brand, *a, **kw):
        calls.append(brand)
        if brand == "Tesla":
            response = requests.Response()
            response.status_code = 429
            raise requests.HTTPError(response=response)
        return []

    monkeypatch.setattr(ingest_run, "fetch_news_mentions", fake_fetch)
    monkeypatch.setattr(ingest_run, "REDDIT_CONFIGURED", False)

    ingest_run.run(brands=["Boeing", "Tesla", "Nvidia"])

    assert calls == ["Boeing", "Tesla", "Nvidia"], "every brand should still be attempted"
    out = capsys.readouterr().out
    assert "rate limit reached" in out
    assert "Tesla" in out
