import sqlite3
from pathlib import Path

from src.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS mentions (
    id TEXT PRIMARY KEY,
    brand TEXT NOT NULL,
    source_type TEXT NOT NULL,      -- 'news' | 'reddit'
    source_name TEXT,               -- outlet name or subreddit
    title TEXT,
    text TEXT,
    url TEXT,
    author TEXT,
    published_at TEXT NOT NULL,     -- ISO 8601
    fetched_at TEXT NOT NULL        -- ISO 8601
);

CREATE INDEX IF NOT EXISTS idx_mentions_brand_date
    ON mentions (brand, published_at);

CREATE TABLE IF NOT EXISTS topics (
    brand TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    keywords TEXT,       -- top keywords for this topic, comma-separated
    size INTEGER,         -- number of mentions currently in this topic
    PRIMARY KEY (brand, topic_id)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    brand TEXT NOT NULL,
    date TEXT NOT NULL,             -- YYYY-MM-DD (UTC)
    mention_count INTEGER,
    dominant_topic INTEGER,
    drift_score REAL,               -- Jensen-Shannon distance vs previous day's topic mix (0-1)
    is_changepoint INTEGER DEFAULT 0,
    PRIMARY KEY (brand, date)
);
"""

# Lightweight migrations: each is safe to re-run, failures (column already
# exists) are ignored. Simpler than a migration framework for a project this size.
MIGRATIONS = [
    "ALTER TABLE mentions ADD COLUMN dedup_group_id TEXT",
    "ALTER TABLE mentions ADD COLUMN is_canonical INTEGER DEFAULT 1",
    "ALTER TABLE mentions ADD COLUMN topic_id INTEGER",
    "ALTER TABLE mentions ADD COLUMN sentiment_label TEXT",
    "ALTER TABLE mentions ADD COLUMN sentiment_score REAL",
    "ALTER TABLE daily_stats ADD COLUMN mean_sentiment REAL",
    "ALTER TABLE daily_stats ADD COLUMN risk_score REAL",
    "ALTER TABLE daily_stats ADD COLUMN risk_band TEXT",
    "ALTER TABLE daily_stats ADD COLUMN drift_component REAL",
    "ALTER TABLE daily_stats ADD COLUMN volume_component REAL",
    "ALTER TABLE daily_stats ADD COLUMN sentiment_component REAL",
    "ALTER TABLE daily_stats ADD COLUMN alerted INTEGER DEFAULT 0",
]


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    for stmt in MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()
    return conn


def upsert_mentions(conn: sqlite3.Connection, mentions: list[dict]) -> int:
    """Insert mentions, skipping ones we already have (by id). Returns rows inserted."""
    cur = conn.executemany(
        """
        INSERT OR IGNORE INTO mentions
            (id, brand, source_type, source_name, title, text, url, author, published_at, fetched_at)
        VALUES
            (:id, :brand, :source_type, :source_name, :title, :text, :url, :author, :published_at, :fetched_at)
        """,
        mentions,
    )
    conn.commit()
    return cur.rowcount
