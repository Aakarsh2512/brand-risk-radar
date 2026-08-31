from datetime import datetime

from src.evaluate.run import match_events, precision


def _d(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def test_match_events_finds_nearby_flagged_day():
    flagged = [_d("2026-01-06"), _d("2026-02-01")]
    events = [_d("2026-01-05"), _d("2026-06-01")]
    matches = match_events(flagged, events, tolerance_days=2)
    assert matches[0] == _d("2026-01-06")
    assert matches[1] is None


def test_precision_counts_only_near_event_days():
    flagged = [_d("2026-01-06"), _d("2026-05-01")]
    events = [_d("2026-01-05")]
    assert precision(flagged, events, tolerance_days=2) == 0.5


def test_precision_with_no_flagged_days_is_zero():
    assert precision([], [_d("2026-01-05")]) == 0.0
