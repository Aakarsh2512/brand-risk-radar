"""Real-world events to check the pipeline's alerts/changepoints against.

Historical backtesting (e.g. against Boeing's Jan-Mar 2024 door-plug crisis)
needed reach-back that every free news API gates behind a paid tier -- GDELT,
GNews, NewsData.io and Currents all cap free lookback at ~30 days like
NewsAPI, and GDELT was unreachable besides. So events are labelled from the
corpus this project actually collected.

HOW THESE WERE LABELLED, AND WHAT THAT MEANS
--------------------------------------------
These were identified by reading the headlines in windows the detector
flagged. That makes them useful for asking "were the alarms real?" but NOT
for "what did we miss?" -- days the detector ignored were never reviewed, so
any recall figure computed against this list is optimistic by construction.

A clean recall number needs a blind pass: sample flagged and unflagged days
together, label them without seeing which is which, then evaluate. That's the
honest next step, and it's deliberately not been shortcut here.

Format: {brand: [(date, description), ...]}
"""
GROUND_TRUTH: dict[str, list[tuple[str, str]]] = {
    "Shein": [
        ("2026-09-08", "Recall of ~963 spiral toys over choking risk (fourth recall since Aug 2025); "
                       "Shein loses $5bn in value in under a week following IPO"),
        ("2026-09-09", "Urgent recall of children's toy over deadly choking risk widely picked up"),
    ],
    "Ryanair": [
        ("2026-09-16", "Backlash over CEO Michael O'Leary's use of the word 'rapists'; separate story "
                       "on refund refused to a bereaved mother"),
    ],
    "TikTok": [
        ("2026-09-16", "TikTok users stalking the family of a holdout juror; platform shut down in "
                       "Equatorial Guinea"),
    ],
    "Coinbase": [
        ("2026-09-10", "Base App rebranded back to Coinbase Wallet after a year, widely covered as a "
                       "retreat from the social experiment"),
    ],
    "Boeing": [],
    "Tesla": [],
    "Nvidia": [],
    "OpenAI": [],
    "Pfizer": [],
    "Starbucks": [],
}
