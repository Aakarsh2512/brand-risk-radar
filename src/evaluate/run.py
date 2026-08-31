"""Evaluates the pipeline's risk-score/changepoint output against
real-world events logged in ground_truth.py -- see that file for why this
checks live data rather than a historical backtest.

For each logged event, was there a system-flagged day (Elevated/Critical
band, or a detected changepoint) within TOLERANCE_DAYS? That's recall.
Precision is the inverse: of the days the system flagged, how many land
near a logged event vs. false-alarming on noise?
"""
from datetime import datetime

from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.evaluate.ground_truth import GROUND_TRUTH

TOLERANCE_DAYS = 2
ALERT_BANDS = {"Elevated", "Critical"}


def _parse(d: str) -> datetime:
    return datetime.strptime(d, "%Y-%m-%d")


def match_events(
    flagged_dates: list[datetime], event_dates: list[datetime], tolerance_days: int = TOLERANCE_DAYS
) -> list[datetime | None]:
    """For each event date, returns the earliest flagged date within
    tolerance (or None if no match). Order matches event_dates.
    """
    results = []
    for event in event_dates:
        candidates = [d for d in flagged_dates if abs((d - event).days) <= tolerance_days]
        results.append(min(candidates) if candidates else None)
    return results


def precision(
    flagged_dates: list[datetime], event_dates: list[datetime], tolerance_days: int = TOLERANCE_DAYS
) -> float:
    if not flagged_dates:
        return 0.0
    true_positives = sum(
        1 for d in flagged_dates if any(abs((d - e).days) <= tolerance_days for e in event_dates)
    )
    return true_positives / len(flagged_dates)


def run() -> None:
    conn = get_connection()
    for brand in TRACKED_BRANDS:
        events = GROUND_TRUTH.get(brand, [])
        rows = conn.execute(
            "SELECT date, risk_band, is_changepoint FROM daily_stats WHERE brand = ? ORDER BY date",
            (brand,),
        ).fetchall()

        if not rows:
            print(f"[{brand}] no daily_stats yet -- run the pipeline first.\n")
            continue
        if not events:
            print(
                f"[{brand}] {len(rows)} days of history, but no ground-truth events logged yet. "
                f"Add real events to src/evaluate/ground_truth.py as they happen.\n"
            )
            continue

        flagged_dates = [_parse(date) for date, band, is_cp in rows if band in ALERT_BANDS or is_cp]
        event_dates = [_parse(d) for d, _ in events]

        print(f"[{brand}] {len(rows)} days of history, {len(flagged_dates)} flagged as Elevated/Critical or a changepoint")

        matches = match_events(flagged_dates, event_dates)
        hits = 0
        for (event_date, description), match in zip(events, matches):
            if match is not None:
                hits += 1
                lead = (_parse(event_date) - match).days
                lead_str = f"{lead} day(s) EARLY" if lead > 0 else (f"{-lead} day(s) LATE" if lead < 0 else "same day")
                print(f"  HIT  {event_date} ({description}) -> flagged {match.date()} ({lead_str})")
            else:
                print(f"  MISS {event_date} ({description}) -> no flagged day within {TOLERANCE_DAYS} days")

        recall = hits / len(events)
        prec = precision(flagged_dates, event_dates)
        print(f"  Recall:    {hits}/{len(events)} logged events matched ({recall:.0%})")
        print(f"  Precision: {prec:.0%} of flagged days landed near a logged event\n")


if __name__ == "__main__":
    run()
