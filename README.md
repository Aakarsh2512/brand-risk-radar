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
8. **API + Dashboard** — FastAPI backend serving risk scores/topics/mentions as JSON,
   consumed by a React (Vite) + Recharts frontend
9. **Evaluation** — checks the risk score/changepoint flags against real events, logged as they happen

## Status

All 9 steps are built and verified end-to-end against live data. `src/pipeline.py`
runs the full chain (ingest → dedup → topics → drift → sentiment → risk → alert)
in one call, and a Windows Scheduled Task runs it daily so real history
accumulates automatically (`scripts/register_task.ps1`).

**On evaluation:** the original plan was to backtest against a documented past
crisis (Boeing's Jan–Mar 2024 737 MAX 9 door-plug incident). That needed
historical news reach-back that turned out to require a paid API — every free
historical news source checked (GDELT, GNews, NewsData.io, Currents) caps free
lookback at ~30 days, and GDELT's API was outright unreachable from testing.
So evaluation instead runs against live, accumulating data: as real news
breaks about a tracked brand, it gets logged in `src/evaluate/ground_truth.py`
with the date it happened, and `python -m src.evaluate.run` reports whether
the pipeline's risk band or changepoint flags caught it, with a tolerance
window for early/late detection.

## Project layout

```
src/           Python pipeline: ingestion, dedup, topic modeling, scoring, API, evaluation
frontend/      React dashboard
scripts/       Daily-run scheduling (Windows Task Scheduler)
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
```

Run the full pipeline (each step reads what the previous one wrote to SQLite):

```bash
python -m src.pipeline
```

To run it automatically once a day (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1
```

To check the evaluation against real logged events:

```bash
python -m src.evaluate.run
```

Then run the API and dashboard (separate terminals):

```bash
uvicorn src.api.main:app --reload --port 8000

cd frontend
npm install
npm run dev   # http://localhost:5173
```
