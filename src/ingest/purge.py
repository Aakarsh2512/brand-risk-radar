"""One-off cleanup: drop legacy mentions that don't name the brand in the
headline.

The first three weeks of collection used NewsAPI's loose `q` parameter, which
matched the brand anywhere in the article body and pulled in ~79% irrelevant
coverage. Ingestion now filters at the source, but those legacy rows are still
in the database skewing every downstream stage, so they get purged once here.

Safe to re-run; safe to undo, since data/mentions.db is versioned in git.

Usage:  python -m src.ingest.purge [--dry-run]
"""
import sys

from src.db import get_connection
from src.ingest.news import is_relevant


def run(dry_run: bool = False) -> None:
    conn = get_connection()
    rows = conn.execute("SELECT id, brand, title, text FROM mentions").fetchall()

    doomed = [r[0] for r in rows if not is_relevant(r[1], r[2], r[3])]
    kept = len(rows) - len(doomed)

    print(f"total mentions:  {len(rows)}")
    print(f"  relevant:      {kept}")
    print(f"  irrelevant:    {len(doomed)}  ({len(doomed)/len(rows):.0%})" if rows else "")

    if dry_run:
        print("\n(dry run -- nothing deleted)")
        return

    conn.executemany("DELETE FROM mentions WHERE id = ?", [(i,) for i in doomed])
    # Derived tables are rebuilt from scratch by the pipeline, so clear them
    # rather than leaving stats computed over the purged corpus.
    conn.execute("DELETE FROM daily_stats")
    conn.execute("DELETE FROM topics")
    conn.commit()
    print(f"\ndeleted {len(doomed)} irrelevant mentions; cleared derived tables")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
