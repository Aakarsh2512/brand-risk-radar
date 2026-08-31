"""Composite PR risk score: combines narrative drift (primary signal),
mention-volume anomaly, and a sentiment dip into a single 0-100 score per
day, banded into Watch / Elevated / Critical.

Weights are deliberately front-loaded toward drift_score -- the premise of
this project is that a narrative pivot (the story changing from "product
defect" to "company response failure") is a stronger and earlier signal
than sentiment or volume moving alone. These weights and the band
thresholds are a reasonable starting point, not something derived from
data; the backtest against a real crisis (step 9) is where they'd actually
get tuned against ground truth.
"""
import statistics

DRIFT_WEIGHT = 0.5
VOLUME_WEIGHT = 0.3
SENTIMENT_WEIGHT = 0.2
CHANGEPOINT_BONUS = 15

MIN_BASELINE_DAYS = 3
BASELINE_WINDOW = 14

WATCH_THRESHOLD = 40
CRITICAL_THRESHOLD = 70


def _volume_component(today_count: int, baseline_counts: list[int]) -> float:
    """0-100. Requires a minimum amount of history to say anything -- with
    too little baseline, a single busy day isn't evidence of an anomaly.
    """
    if len(baseline_counts) < MIN_BASELINE_DAYS:
        return 0.0
    mean = statistics.mean(baseline_counts)
    stdev = statistics.pstdev(baseline_counts)
    if stdev == 0:
        return 0.0
    z = (today_count - mean) / stdev
    return max(0.0, min(z, 3.0)) / 3.0 * 100


def _sentiment_component(today_sentiment: float, baseline_sentiments: list[float]) -> float:
    """0-100, based on how far today's sentiment dropped below the recent
    baseline (not its absolute value -- a brand with normally-neutral
    coverage that turns neutral-to-slightly-negative is more informative
    than a fixed "sentiment < 0" cutoff).
    """
    if not baseline_sentiments:
        return 0.0
    baseline_mean = statistics.mean(baseline_sentiments)
    drop = baseline_mean - today_sentiment  # positive = got worse
    return max(0.0, min(drop, 2.0)) / 2.0 * 100


def _band(score: float) -> str:
    if score >= CRITICAL_THRESHOLD:
        return "Critical"
    if score >= WATCH_THRESHOLD:
        return "Elevated"
    return "Watch"


def score_day(
    drift_score: float,
    is_changepoint: bool,
    today_count: int,
    baseline_counts: list[int],
    today_sentiment: float,
    baseline_sentiments: list[float],
) -> dict:
    drift_component = drift_score * 100
    volume_component = _volume_component(today_count, baseline_counts)
    sentiment_component = _sentiment_component(today_sentiment, baseline_sentiments)

    raw = (
        DRIFT_WEIGHT * drift_component
        + VOLUME_WEIGHT * volume_component
        + SENTIMENT_WEIGHT * sentiment_component
    )
    if is_changepoint:
        raw += CHANGEPOINT_BONUS
    score = max(0.0, min(raw, 100.0))

    return {
        "score": score,
        "band": _band(score),
        "drift_component": drift_component,
        "volume_component": volume_component,
        "sentiment_component": sentiment_component,
        "changepoint_bonus": CHANGEPOINT_BONUS if is_changepoint else 0,
    }
