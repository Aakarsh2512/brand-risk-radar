"""Generates a short, human-readable explanation for a brand's current risk
band, naming the specific signal(s) driving it. Uses an LLM if
ANTHROPIC_API_KEY is set; otherwise falls back to a deterministic template
built directly from the same numbers, so the alert step works end-to-end
without an API key.
"""
from src.config import ANTHROPIC_API_KEY


def _template_explanation(
    brand: str,
    band: str,
    score: float,
    drift_score: float,
    is_changepoint: bool,
    volume_component: float,
    sentiment_component: float,
    top_keywords: str,
) -> str:
    parts = [f"{brand} risk is {band} ({score:.0f}/100)."]
    if is_changepoint:
        parts.append("The narrative shifted today (changepoint detected).")
    if drift_score > 0.3:
        parts.append(f"Topic drift is elevated ({drift_score:.2f}); current focus: {top_keywords}.")
    if volume_component > 30:
        parts.append("Mention volume is anomalously high vs. the recent baseline.")
    if sentiment_component > 30:
        parts.append("Sentiment has dropped noticeably below its recent baseline.")
    if len(parts) == 1:
        parts.append("No single signal dominates; the score is a blend of moderate movement across drift, volume, and sentiment.")
    return " ".join(parts)


def explain(
    brand: str,
    band: str,
    score: float,
    drift_score: float,
    is_changepoint: bool,
    volume_component: float,
    sentiment_component: float,
    top_keywords: str,
) -> str:
    fallback = _template_explanation(
        brand, band, score, drift_score, is_changepoint, volume_component, sentiment_component, top_keywords
    )
    if not ANTHROPIC_API_KEY:
        return fallback

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = (
            f"Brand: {brand}\n"
            f"Risk band: {band} (score {score:.0f}/100)\n"
            f"Narrative drift score: {drift_score:.2f} (0 = same story as yesterday, 1 = completely different)\n"
            f"Changepoint detected today: {is_changepoint}\n"
            f"Volume-anomaly component: {volume_component:.0f}/100\n"
            f"Sentiment-dip component: {sentiment_component:.0f}/100\n"
            f"Current dominant topic keywords: {top_keywords}\n\n"
            "Write a 2-sentence explanation a PR/comms professional could read "
            "at a glance to understand why this alert fired. Be specific about "
            "which signal is driving it. No preamble."
        )
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:  # noqa: BLE001 -- alerting should never crash on the LLM step
        return fallback + f" (LLM explanation unavailable: {e})"
