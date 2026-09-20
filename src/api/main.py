"""FastAPI backend: serves the pipeline's SQLite data as JSON for the React
dashboard. Read-only -- all the actual computation happens in the pipeline
modules (src/ingest, src/dedup, src/topics, src/drift, src/sentiment,
src/risk); this just exposes the results.

Run with: uvicorn src.api.main:app --reload
"""
import os
import re
from collections import Counter

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import TRACKED_BRANDS
from src.db import get_connection
from src.ingest.news import fetch_news_mentions

app = FastAPI(title="Brand Risk Radar API")

allowed_origins = ["http://localhost:5173"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/brands")
def list_brands():
    return {"brands": TRACKED_BRANDS}


VALID_BRAND = re.compile(r"^[\w .&'-]{2,40}$")


@app.get("/api/preview/{brand}")
def preview(brand: str):
    """Live look at any brand, tracked or not.

    This deliberately stops short of a risk score. Narrative drift is measured
    against a brand's *own* baseline churn, so it needs roughly two weeks of
    history before it means anything -- and the deployed API runs without the
    ML dependencies (torch, BERTopic) so it fits a free 512MB instance. What
    can be answered instantly is "what is being written about this brand right
    now, and how much of it", which is what this returns.
    """
    name = brand.strip()
    if not VALID_BRAND.match(name):
        raise HTTPException(status_code=400, detail="Brand names are 2-40 letters, digits or spaces.")

    try:
        mentions = fetch_news_mentions(name)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            raise HTTPException(
                status_code=503,
                detail="The news API's daily free quota is used up. It resets every 24 hours.",
            )
        raise HTTPException(status_code=502, detail="The news API rejected that request.")
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Could not reach the news API.")

    by_day = Counter(m["published_at"][:10] for m in mentions)
    daily_volume = [{"date": d, "count": n} for d, n in sorted(by_day.items())]

    return {
        "brand": name,
        "preview": True,
        "tracked": name in TRACKED_BRANDS,
        "article_count": len(mentions),
        "daily_volume": daily_volume,
        "articles": [
            {
                "title": m["title"],
                "source_name": m["source_name"],
                "url": m["url"],
                "published_at": m["published_at"],
            }
            for m in mentions
        ],
    }


@app.get("/api/daily-stats/{brand}")
def daily_stats(brand: str):
    conn = get_connection()
    columns = [
        "date", "mention_count", "window_mentions", "drift_score", "drift_z",
        "is_changepoint", "mean_sentiment", "risk_score", "risk_band",
        "drift_component", "volume_component", "sentiment_component",
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
