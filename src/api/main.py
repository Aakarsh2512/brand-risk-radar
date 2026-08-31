"""FastAPI backend: serves the pipeline's SQLite data as JSON for the React
dashboard. Read-only -- all the actual computation happens in the pipeline
modules (src/ingest, src/dedup, src/topics, src/drift, src/sentiment,
src/risk); this just exposes the results.

Run with: uvicorn src.api.main:app --reload
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import TRACKED_BRANDS
from src.db import get_connection

app = FastAPI(title="Brand Risk Radar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/brands")
def list_brands():
    return {"brands": TRACKED_BRANDS}


@app.get("/api/daily-stats/{brand}")
def daily_stats(brand: str):
    conn = get_connection()
    columns = [
        "date", "mention_count", "drift_score", "is_changepoint", "mean_sentiment",
        "risk_score", "risk_band", "drift_component", "volume_component", "sentiment_component",
    ]
    rows = conn.execute(
        f"SELECT {', '.join(columns)} FROM daily_stats WHERE brand = ? ORDER BY date",
        (brand,),
    ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for brand '{brand}'")
    return [dict(zip(columns, row)) for row in rows]


@app.get("/api/topics/{brand}")
def topics(brand: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT topic_id, keywords, size FROM topics WHERE brand = ? ORDER BY size DESC",
        (brand,),
    ).fetchall()
    return [{"topic_id": r[0], "keywords": r[1], "size": r[2]} for r in rows]


@app.get("/api/mentions/{brand}")
def mentions(brand: str, date: str | None = None, limit: int = 50):
    columns = ["title", "source_name", "url", "published_at", "sentiment_label", "sentiment_score", "topic_id"]
    query = f"""
        SELECT {', '.join(columns)} FROM mentions
        WHERE brand = ? AND is_canonical = 1
    """
    params: list = [brand]
    if date:
        query += " AND date(published_at) = ?"
        params.append(date)
    query += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    return [dict(zip(columns, row)) for row in rows]
