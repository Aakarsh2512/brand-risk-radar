import requests
from fastapi.testclient import TestClient

from src.api import main as api

client = TestClient(api.app, raise_server_exceptions=False)


def _article(title, day, source="Example News"):
    return {
        "title": title,
        "source_name": source,
        "url": f"https://example.com/{title.replace(' ', '-')}",
        "published_at": f"2026-09-{day:02d}T09:00:00Z",
        "text": "",
    }


def test_preview_rejects_nonsense_brand_names():
    for bad in ("x", "!!!", "a" * 41):
        assert client.get(f"/api/preview/{bad}").status_code == 400


def test_preview_summarises_daily_volume(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_news_mentions",
        lambda brand, **kw: [
            _article("Airbnb under scrutiny", 17),
            _article("Airbnb hosts protest", 17),
            _article("Airbnb earnings beat", 18),
        ],
    )

    body = client.get("/api/preview/Airbnb").json()

    assert body["brand"] == "Airbnb"
    assert body["preview"] is True
    assert body["tracked"] is False
    assert body["article_count"] == 3
    assert body["daily_volume"] == [
        {"date": "2026-09-17", "count": 2},
        {"date": "2026-09-18", "count": 1},
    ]
    assert len(body["articles"]) == 3


def test_preview_flags_a_brand_we_already_track(monkeypatch):
    monkeypatch.setattr(api, "fetch_news_mentions", lambda brand, **kw: [])
    assert client.get("/api/preview/Boeing").json()["tracked"] is True


def test_preview_translates_a_rate_limit_into_a_readable_error(monkeypatch):
    def rate_limited(brand, **kw):
        response = requests.Response()
        response.status_code = 429
        raise requests.HTTPError(response=response)

    monkeypatch.setattr(api, "fetch_news_mentions", rate_limited)

    r = client.get("/api/preview/Airbnb")
    assert r.status_code == 503
    assert "quota" in r.json()["detail"].lower()


def test_preview_survives_the_news_api_being_unreachable(monkeypatch):
    def unreachable(brand, **kw):
        raise requests.ConnectionError()

    monkeypatch.setattr(api, "fetch_news_mentions", unreachable)
    assert client.get("/api/preview/Airbnb").status_code == 502
