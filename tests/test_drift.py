"""Validates drift scoring, normalization, and changepoint detection against
synthetic series with known shape.
"""
from src.drift.changepoint import compute_drift_scores, detect_changepoints, normalize_drift
from src.drift.topic_distribution import build_windowed_topic_distribution


def test_stable_topic_mix_has_near_zero_drift():
    distribution = [[0.9, 0.1]] * 10
    scores = compute_drift_scores(distribution)
    assert all(s < 0.01 for s in scores)


def test_detects_changepoint_at_a_topic_shift():
    # Days 0-9: mostly topic A ("product defect" style coverage).
    # Days 10-19: mostly topic B ("company response" style coverage).
    distribution = [[0.9, 0.1]] * 10 + [[0.1, 0.9]] * 10

    scores = compute_drift_scores(distribution)
    assert max(scores) > 0.5, "expected a large drift score right at the shift"

    changepoints = detect_changepoints(distribution)
    assert changepoints, "expected at least one changepoint to be flagged"
    assert any(8 <= cp <= 12 for cp in changepoints), (
        f"expected a changepoint near day 10, got {changepoints}"
    )


def test_normalization_flattens_a_constantly_churny_brand():
    """The bug that broke the first version: a brand whose topic mix always
    churns produces a high raw distance every day. Normalized, that's
    unremarkable -- and must not read as a permanent alarm.
    """
    steady_churn = [0.70] * 15
    z = normalize_drift(steady_churn)
    assert all(abs(v) < 0.5 for v in z), f"constant churn should normalize to ~0, got {z}"


def test_normalization_still_surfaces_a_genuine_spike():
    scores = [0.30, 0.28, 0.31, 0.29, 0.30, 0.32, 0.29, 0.85]
    z = normalize_drift(scores)
    assert z[-1] > 3, f"a jump well outside the brand's norm should score high, got {z[-1]}"


def test_normalization_waits_for_enough_baseline():
    z = normalize_drift([0.5, 0.9, 0.2])
    assert z == [0.0, 0.0, 0.0], "without baseline history there's nothing to normalize against"


def test_windowed_distribution_smooths_single_day_noise():
    # One mention per day, alternating topics: day-over-day this looks like
    # total upheaval, but a trailing window shows a stable 50/50 mix.
    rows = []
    for day in range(1, 15):
        rows.append((f"2026-09-{day:02d}T12:00:00Z", day % 2))

    _dates, _topics, windowed, _totals = build_windowed_topic_distribution(rows, window_days=7)
    drift = compute_drift_scores(windowed, lag=7)
    assert max(drift) < 0.3, f"windowing should suppress alternating-day noise, got {max(drift)}"


def test_thin_windows_are_not_scored():
    """Regression test: a window holding a couple of articles can swing from
    one topic to another on a single publication. Normalizing that against
    other noise produced a +8 sigma "alarm" on two articles.
    """
    scores = [0.30, 0.28, 0.31, 0.29, 0.30, 0.32, 0.85]
    reliable = [True, True, True, True, True, True, False]  # last window too thin
    z = normalize_drift(scores, reliable=reliable)
    assert z[-1] == 0.0, "a spike on too little data must not score"
