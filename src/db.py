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
"""


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
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
