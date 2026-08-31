"""Real-world events to check the pipeline's alerts/changepoints against.

Historical backtesting (e.g. against Boeing's Jan-Mar 2024 door-plug
crisis) turned out to need a paid news API -- every free historical news
API we checked (GDELT, GNews, NewsData.io, Currents) caps free-tier
lookback at ~30 days, same as NewsAPI, and GDELT's API was outright
unreachable from this network. Rather than pay for one, this project
evaluates against live data instead: as real news breaks about a tracked
brand, add it here with the date it happened, then run
`python -m src.evaluate.run` to check whether the pipeline's risk score
or changepoint flags caught it.

Format: {brand: [(date, description), ...]}
"""
GROUND_TRUTH: dict[str, list[tuple[str, str]]] = {
    "Boeing": [
        # ("2026-09-15", "e.g. FAA opens new investigation into ..."),
    ],
}
