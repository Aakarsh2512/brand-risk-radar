from src.alert.explain import explain
from src.alert.slack import send_alert


def test_explain_falls_back_to_template_without_api_key(monkeypatch):
    monkeypatch.setattr("src.alert.explain.ANTHROPIC_API_KEY", None)
    text = explain(
        brand="Boeing",
        band="Critical",
        score=85.0,
        drift_score=0.9,
        is_changepoint=True,
        volume_component=10.0,
        sentiment_component=5.0,
        top_keywords="recall, faa, grounded",
    )
    assert "Boeing" in text
    assert "Critical" in text
    assert "changepoint" in text.lower()


def test_send_alert_without_webhook_prints_instead_of_raising(monkeypatch, capsys):
    monkeypatch.setattr("src.alert.slack.SLACK_WEBHOOK_URL", None)
    send_alert("test message")
    captured = capsys.readouterr()
    assert "test message" in captured.out
