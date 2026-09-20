"""Guards the reproducibility of topic assignment.

Drift is measured over the topic distribution, and the daily job recomputes
the whole history from scratch every run. So a non-deterministic topic model
doesn't just jitter today's number -- it rewrites every past day's drift score
too. Two runs over the same corpus once disagreed on whether a day was a
+7.6 sigma spike or a +2.9 one.
"""
import pytest

from src.topics.model import fit_topic_model

CORPUS = (
    [f"Regulator opens safety investigation into the company, filing {i}" for i in range(14)]
    + [f"Company announces record quarterly earnings beat, report {i}" for i in range(14)]
    + [f"Chief executive steps down amid mounting pressure, story {i}" for i in range(14)]
)


@pytest.mark.slow
def test_topic_assignment_is_reproducible():
    first = list(fit_topic_model(CORPUS).topics_)
    second = list(fit_topic_model(CORPUS).topics_)
    assert first == second, "same corpus must yield the same topic assignment across runs"
