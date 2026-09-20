"""Narrative drift scoring, normalization, and changepoint detection.

drift_score(t) = Jensen-Shannon distance between the topic distribution at t
and the one `lag` steps earlier. Bounded [0, 1]: 0 means the same mix of
stories, 1 means a completely different one.

The raw distance alone is not a usable alarm signal. Every brand has its own
resting level of churn -- a company covered by a rotating cast of minor stories
sits naturally high, one with steady coverage sits low -- so a fixed threshold
either alarms constantly on the first or never fires on the second. In the
first run of this project the raw score sat at a mean of 0.70 across every
single day, which pushed 54% of days into "Elevated" and left the changepoint
detector with no segments to find.

So drift is normalized into a z-score against *each brand's own* recent
history. What matters is not "how different is today" but "how different is
today, for this brand, compared to how different it usually is".

The baseline deliberately uses only days *before* the one being scored. Using
the full series would leak future information into a historical score and
flatter the results.
"""
import numpy as np
import ruptures as rpt
from scipy.spatial.distance import jensenshannon

MIN_POINTS_FOR_PELT = 8
MIN_BASELINE_POINTS = 5


def compute_drift_scores(distribution: list[list[float]], lag: int = 1) -> list[float]:
    """One score per entry. The first `lag` entries are 0.0 -- nothing to
    compare against yet.
    """
    scores = [0.0] * min(lag, len(distribution))
    for i in range(lag, len(distribution)):
        dist = jensenshannon(distribution[i - lag], distribution[i], base=2)
        scores.append(0.0 if np.isnan(dist) else float(dist))
    return scores


def normalize_drift(
    scores: list[float],
    min_baseline: int = MIN_BASELINE_POINTS,
    reliable: list[bool] | None = None,
) -> list[float]:
    """Convert raw drift into a trailing z-score against the same brand's
    history. Returns 0.0 until there's enough baseline to judge against.

    `reliable` marks which points rest on enough underlying data to mean
    anything. Unreliable points score 0.0 and are kept out of the baseline:
    a window holding two articles can swing from one topic to another on a
    single publication, and normalizing that noise against other noise
    manufactures very confident-looking z-scores out of nothing.
    """
    if reliable is None:
        reliable = [True] * len(scores)

    normalized = []
    for i, score in enumerate(scores):
        if not reliable[i]:
            normalized.append(0.0)
            continue
        baseline = [s for j, s in enumerate(scores[:i]) if s > 0 and reliable[j]]
        if len(baseline) < min_baseline:
            normalized.append(0.0)
            continue
        mean = float(np.mean(baseline))
        std = float(np.std(baseline))
        # Guard against near-zero rather than exactly zero: np.std over
        # identical values returns ~1e-17, not 0.0, and dividing by that turns
        # floating-point dust into a confident-looking z-score.
        normalized.append(0.0 if std < 1e-9 else (score - mean) / std)
    return normalized


def detect_changepoints(distribution: list[list[float]], pen: float = 3) -> list[int]:
    """Indices where the topic distribution itself shifts regime.

    PELT runs on the distribution series rather than the drift diffs: a shift
    shows up in the diffs as one isolated spike, which is a point anomaly, not
    the segment change PELT is built to find.
    """
    if len(distribution) < MIN_POINTS_FOR_PELT:
        return []

    signal = np.array(distribution)
    algo = rpt.Pelt(model="rbf").fit(signal)
    breakpoints = algo.predict(pen=pen)
    return [b for b in breakpoints if b < len(distribution)]
