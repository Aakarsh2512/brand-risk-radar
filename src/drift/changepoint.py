"""Narrative drift scoring and changepoint detection.

drift_score(day t) = Jensen-Shannon distance between day t's topic
distribution and day t-1's. It's bounded [0, 1]: 0 means the story is about
the same mix of topics as the day before, 1 means it's a completely
different story. This is the signal that "sentiment stayed flat but the
narrative moved on" would show up in.

On top of the drift-score series, we run PELT (Pruned Exact Linear Time,
via the `ruptures` library) to flag specific days where the *overall*
narrative shifted -- not just noisy day-to-day wobble. PELT needs a
reasonable number of data points to be meaningful; below MIN_POINTS_FOR_PELT
we skip it and just report the raw drift scores.
"""
import numpy as np
import ruptures as rpt
from scipy.spatial.distance import jensenshannon

MIN_POINTS_FOR_PELT = 8


def compute_drift_scores(distribution: list[list[float]]) -> list[float]:
    """Returns one score per day; day 0 is always 0.0 (nothing to compare to)."""
    scores = [0.0]
    for i in range(1, len(distribution)):
        dist = jensenshannon(distribution[i - 1], distribution[i], base=2)
        scores.append(0.0 if np.isnan(dist) else float(dist))
    return scores


def detect_changepoints(distribution: list[list[float]]) -> list[int]:
    """Returns day-indices flagged as changepoints in the topic distribution
    itself (not the derived drift-score diff -- a single-day spike in the
    diff signal is a point anomaly, not a segment shift, and PELT is built
    to find shifts in a segment's underlying statistics). Empty if there
    isn't enough history to detect changepoints reliably.
    """
    if len(distribution) < MIN_POINTS_FOR_PELT:
        return []

    signal = np.array(distribution)
    algo = rpt.Pelt(model="rbf").fit(signal)
    # `pen` (penalty) controls sensitivity; higher = fewer, more confident
    # changepoints.
    breakpoints = algo.predict(pen=3)
    return [b for b in breakpoints if b < len(distribution)]
