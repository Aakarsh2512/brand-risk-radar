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

# Brands to track. Chosen for two reasons: they generate enough English news
# volume to support daily topic modeling, and their names are unambiguous in a
# headline (unlike "Apple" or "Meta", which match fruit and meta-analysis).
# Tracking ~10 brands instead of 1 is deliberate: a crisis detector can only be
# evaluated on a window that actually contains an escalation, and the odds of
# catching one scale with the number of brands under watch.
TRACKED_BRANDS = [
    "Boeing",
    "Tesla",
    "Nvidia",
    "OpenAI",
    "Ryanair",
    "Shein",
    "TikTok",
    "Coinbase",
    "Pfizer",
    "Starbucks",
]

# A mention only counts if the brand name appears in the headline. Loose
# full-text matching (NewsAPI's `q`) pulled in ~79% irrelevant articles, which
# saturated the drift signal and made the whole risk score meaningless.
RELEVANCE_REQUIRES_BRAND_IN_TITLE = True
