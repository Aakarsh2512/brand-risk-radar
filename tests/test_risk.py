from src.risk.score import score_day


def test_calm_day_stays_in_watch_band():
    result = score_day(
        drift_score=0.05,
        is_changepoint=False,
        today_count=10,
        baseline_counts=[9, 11, 10, 10, 9],
        today_sentiment=0.0,
        baseline_sentiments=[0.0, 0.1, -0.1, 0.0],
    )
    assert result["band"] == "Watch"
    assert result["score"] < 40


def test_narrative_shift_with_changepoint_reaches_critical():
    result = score_day(
        drift_score=0.9,
        is_changepoint=True,
        today_count=12,
        baseline_counts=[10, 11, 9, 10],
        today_sentiment=-0.3,
        baseline_sentiments=[0.1, 0.0, 0.1, 0.05],
    )
    assert result["band"] == "Critical"
    assert result["score"] >= 70


def test_volume_spike_alone_raises_score_but_needs_baseline():
    baseline = [8, 9, 10, 9, 8]
    calm = score_day(0.05, False, 9, baseline, 0.0, [0.0] * 5)
    spike = score_day(0.05, False, 40, baseline, 0.0, [0.0] * 5)
    assert spike["score"] > calm["score"]

    # Without enough baseline history, a busy day shouldn't be treated as
    # anomalous -- there's nothing to compare it to yet.
    no_baseline = score_day(0.05, False, 40, [], 0.0, [])
    assert no_baseline["volume_component"] == 0.0
