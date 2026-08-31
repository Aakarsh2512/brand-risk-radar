"""Runs the full pipeline once, end to end, for the tracked brands:
ingest -> dedup -> topics -> drift -> sentiment -> risk -> alert.

This is what accumulates daily history for the evaluation step. Schedule
it to run once a day (see scripts/run_daily.bat + scripts/register_task.ps1)
rather than running it continuously -- a brand's news volume doesn't
change meaningfully more often than that, and NewsAPI's free tier has a
daily request cap.
"""
from src.alert.run import run as run_alert
from src.dedup.run import run as run_dedup
from src.drift.run import run as run_drift
from src.ingest.run import run as run_ingest
from src.risk.run import run as run_risk
from src.sentiment.run import run as run_sentiment
from src.topics.run import run as run_topics


def main() -> None:
    print("=== ingest ===")
    run_ingest()
    print("=== dedup ===")
    run_dedup()
    print("=== topics ===")
    run_topics()
    print("=== drift ===")
    run_drift()
    print("=== sentiment ===")
    run_sentiment()
    print("=== risk ===")
    run_risk()
    print("=== alert ===")
    run_alert()


if __name__ == "__main__":
    main()
