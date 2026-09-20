# Brand Risk Radar

**Live demo:** [brand-risk-radar.vercel.app](https://brand-risk-radar.vercel.app/)
(backend: [brand-risk-radar-api.onrender.com](https://brand-risk-radar-api.onrender.com/api/brands) —
free-tier, may take ~30-60s to wake up on first load)

An early-warning system for PR crises. Instead of only tracking whether sentiment
about a brand is positive or negative, this project tracks **what the story is
about** and detects when that narrative shifts — e.g. from "product defect" to
"company response failure" to "executive accountability." That topic pivot is
often a stronger, earlier signal of an escalating crisis than sentiment alone.

## Pipeline

1. **Ingest** — pull brand mentions from NewsAPI (headline-matched) + Reddit (PRAW).
   `src/ingest/backfill.py` pulls a month of history up front, splitting any
   window that hits the API's result cap
2. **Dedup** — sentence embeddings + cosine similarity to merge near-duplicate coverage
3. **Topic extraction** — BERTopic to find each window's dominant narrative(s)
4. **Drift detection** — Jensen-Shannon distance between 7-day topic windows,
   normalized to a z-score against the brand's own churn, plus PELT changepoints
5. **Sentiment** — transformer classifier, used as a supporting signal
6. **Composite risk score** — volume anomaly + topic drift + sentiment, banded Watch/Elevated/Critical
7. **Alerting** — Slack webhook with an auto-generated explanation of the score
8. **API + Dashboard** — FastAPI backend serving risk scores/topics/mentions as JSON,
   consumed by a React (Vite) + Recharts frontend
9. **Evaluation** — `src/evaluate/compare.py` runs drift, volume and sentiment as
   independent detectors head-to-head; `src/evaluate/run.py` scores flags against
   labelled events

## Findings

Run over **3,835 relevant mentions across 10 brands** (~30 days), the three
signals behave as independent detectors, each firing at z ≥ 2 against that
brand's own history (`python -m src.evaluate.compare`):

| detector  | days fired | rate |
|-----------|-----------:|-----:|
| drift     | 8          | 3.1% |
| volume    | 13         | 5.0% |
| sentiment | 8          | 3.1% |

**Drift and sentiment overlapped on zero days.** They are orthogonal — each
catches events the other completely misses, which is the clearest support for
the premise that sentiment monitoring alone leaves a real gap.

Events drift caught that sentiment did not:

- **Shein, 8–10 Sep** — a children's toy recalled over a choking risk (the
  fourth recall since Aug 2025) alongside a $5bn drop in value after IPO.
  Drift fired at **+7.6σ**; sentiment over the same window read **+0.4σ**,
  i.e. nothing. One flag landed **2 days before** the recall coverage peaked.
- **Ryanair, 16 Sep** — backlash over the CEO's use of the word "rapists",
  plus a refund refused to a bereaved mother. Drift **+7.8σ**, sentiment
  **−1.4σ** (moving the *wrong* way).
- **TikTok, 16 Sep** — users stalking a holdout juror's family. Drift **+3.1σ**,
  sentiment **−0.8σ**.

Honest caveats: drift detects *narrative change*, which is necessary but not
sufficient for *risk* — it also fired on Coinbase's Base App rebrand, real news
but not a crisis. And the labelled events in `src/evaluate/ground_truth.py`
were found by reading flagged windows, so recall figures against them are
optimistic by construction; a blind labelling pass over flagged and unflagged
days together is the honest next step.

## What the first version got wrong

Worth recording, because the fixes are most of the engineering:

- **86% of the corpus wasn't about the brand.** NewsAPI's loose `q` matched the
  brand anywhere in the body, pulling in a metal band's tour and exam results
  as "Boeing" coverage. Ingestion now matches on the headline (`qInTitle`).
- **The drift metric was saturated.** Raw Jensen-Shannon distance sat at a mean
  of 0.70 every single day, pushing **54% of days into "Elevated"** and leaving
  the changepoint detector with no segments to find — it never fired once in 24
  days. Drift is now a z-score against each brand's own churn; the alarm rate
  fell to **3%**.
- **Day-over-day comparison measured publishing noise**, not narrative. Now
  compares 7-day windows.
- **Thin windows manufactured confident nonsense** — a 2-article window scored
  +8σ. Windows below 10 mentions no longer score.
- **The drift step wiped columns other steps owned** (`alerted`,
  `mean_sentiment`) by rebuilding `daily_stats` each run, silently zeroing the
  sentiment term. They're now carried across the rebuild.
- **Backfill silently truncated high-volume brands** — a 7-day window that hits
  NewsAPI's 100-result cap returns only the newest slice, collapsing a week
  into a day. Windows now split when `totalResults` exceeds the cap.

## Status

All 9 steps are built and verified end-to-end against live data.
`src/pipeline.py` runs the full chain in one call; GitHub Actions runs it daily
(20/20 successful runs to date) and commits fresh data, which auto-deploys.

The original plan was to backtest against Boeing's Jan–Mar 2024 door-plug
crisis. Every free historical news source checked (GDELT, GNews, NewsData.io,
Currents) caps free lookback at ~30 days, and GDELT was unreachable besides —
so the project instead tracks 10 brands at once, on the logic that a crisis
detector can only be evaluated on a window that contains an escalation, and
those odds scale with the number of brands watched.

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
