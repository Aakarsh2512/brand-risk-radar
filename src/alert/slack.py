"""Sends a PR risk alert to Slack via an incoming webhook. If no webhook is
configured, prints the message instead -- so this step is fully testable
without real Slack setup.
"""
import requests

from src.config import SLACK_WEBHOOK_URL


def send_alert(text: str) -> None:
    if not SLACK_WEBHOOK_URL:
        print("[slack] SLACK_WEBHOOK_URL not set, would have sent:")
        print(text)
        return
    resp = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    resp.raise_for_status()
