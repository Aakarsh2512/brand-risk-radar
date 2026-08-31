"""Validates changepoint detection against a synthetic, known narrative
shift. Our real (live NewsAPI free-tier) Boeing data only spans ~4 days,
too short to prove drift detection works -- so we prove it here instead.
"""
from src.drift.changepoint import compute_drift_scores, detect_changepoints


def test_stable_topic_mix_has_near_zero_drift():
    distribution = [[0.9, 0.1]] * 10
    scores = compute_drift_scores(distribution)
    assert all(s < 0.01 for s in scores)


def test_detects_changepoint_at_a_topic_shift():
    # Days 0-9: mostly topic A ("product defect" style coverage).
    # Days 10-19: mostly topic B ("company response" style coverage).
    stable_a = [[0.9, 0.1]] * 10
    stable_b = [[0.1, 0.9]] * 10
    distribution = stable_a + stable_b

    scores = compute_drift_scores(distribution)
    assert max(scores) > 0.5, "expected a large drift score right at the shift"

    changepoints = detect_changepoints(distribution)
    assert changepoints, "expected at least one changepoint to be flagged"
    assert any(8 <= cp <= 12 for cp in changepoints), (
        f"expected a changepoint near day 10, got {changepoints}"
    )
