import os
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "brand-risk-radar/0.1")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DB_PATH = os.getenv("DB_PATH", "data/mentions.db")

# Brands to track. Edit this list for whichever brand(s) you're backtesting/monitoring.
TRACKED_BRANDS = ["Boeing"]
