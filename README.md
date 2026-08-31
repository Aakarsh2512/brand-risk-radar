# Brand Risk Radar

An early-warning system for PR crises. Instead of only tracking whether sentiment
about a brand is positive or negative, this project tracks **what the story is
about** and detects when that narrative shifts — e.g. from "product defect" to
"company response failure" to "executive accountability." That topic pivot is
often a stronger, earlier signal of an escalating crisis than sentiment alone.

## Pipeline

1. **Ingest** — pull brand mentions from NewsAPI + Reddit (PRAW)
2. **Dedup** — sentence embeddings + cosine similarity to merge near-duplicate coverage
3. **Topic extraction** — BERTopic to find each day's dominant narrative(s)
4. **Drift detection** — changepoint detection on the topic-distribution time series
5. **Sentiment** — transformer classifier, used as a supporting signal
6. **Composite risk score** — volume anomaly + topic drift + sentiment, banded Watch/Elevated/Critical
7. **Alerting** — Slack webhook with an auto-generated explanation of the score
8. **Dashboard** — Streamlit view of risk trajectory, topics over time, flagged mentions
9. **Evaluation** — backtest against a real, documented brand crisis; precision/recall of alert timing

## Status

🚧 Work in progress, built incrementally module by module.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
```
