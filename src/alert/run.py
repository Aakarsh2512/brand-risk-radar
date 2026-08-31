"""Entry point for the alerting step: for each brand, check the latest
day's risk band and -- if Elevated or Critical -- generate an explanation
and send a Slack alert. Skips brands already alerted for that day (tracked
via the `alerted` column) so re-running the pipeline doesn't spam the same
alert. Run this last, after the risk-score step.
"""
from src.alert.explain import explain
from src.alert.slack import send_alert
from src.config import TRACKED_BRANDS
from src.db import get_connection

ALERT_BANDS = {"Elevated", "Critical"}


def run() -> None:
    conn = get_connection()
    for brand in TRACKED_BRANDS:
        row = conn.execute(
            """
            SELECT date, risk_score, risk_band, drift_score, is_changepoint,
                   drift_component, volume_component, sentiment_component,
                   dominant_topic, alerted
            FROM daily_stats WHERE brand = ? ORDER BY date DESC LIMIT 1
            """,
            (brand,),
        ).fetchone()
        if not row:
            print(f"[{brand}] no daily_stats yet, skipping")
            continue

        (date, score, band, drift_score, is_cp,
         drift_component, volume_component, sentiment_component,
         dominant_topic, alerted) = row

        if band not in ALERT_BANDS:
            print(f"[{brand}] {date}: {band}, no alert needed")
            continue
        if alerted:
            print(f"[{brand}] {date}: {band}, already alerted")
            continue

        topic_row = conn.execute(
            "SELECT keywords FROM topics WHERE brand = ? AND topic_id = ?",
            (brand, dominant_topic),
        ).fetchone()
        top_keywords = topic_row[0] if topic_row else "unknown"

        message_body = explain(
            brand=brand,
            band=band,
            score=score,
            drift_score=drift_score or 0.0,
            is_changepoint=bool(is_cp),
            volume_component=volume_component or 0.0,
            sentiment_component=sentiment_component or 0.0,
            top_keywords=top_keywords,
        )
        text = f":rotating_light: *{brand} PR Risk Alert -- {band}* ({score:.0f}/100)\n{message_body}"
        send_alert(text)

        conn.execute("UPDATE daily_stats SET alerted = 1 WHERE brand = ? AND date = ?", (brand, date))
        conn.commit()
        print(f"[{brand}] {date}: {band} alert sent")


if __name__ == "__main__":
    run()
