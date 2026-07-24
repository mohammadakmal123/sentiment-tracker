"""
database.py
SQLite persistence layer for the Sentiment Tracker.

Schema:
    companies(id, name, ticker, created_at)
    headlines(id, company_id, source, headline, url, published_at,
              sentiment_label, compound_score, pos, neu, neg, fetched_at)
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sentiment.db")


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ticker TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS headlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                source TEXT,
                headline TEXT NOT NULL,
                url TEXT,
                published_at TEXT,
                sentiment_label TEXT NOT NULL,
                compound_score REAL NOT NULL,
                pos REAL, neu REAL, neg REAL,
                fetched_at TEXT NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)


def upsert_company(name, ticker):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM companies WHERE ticker = ?", (ticker,)
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO companies (name, ticker, created_at) VALUES (?, ?, ?)",
            (name, ticker, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def list_companies():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, ticker, created_at FROM companies ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


def get_company_by_ticker(ticker):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, ticker FROM companies WHERE ticker = ?", (ticker,)
        ).fetchone()
        return dict(row) if row else None


def headline_exists(company_id, headline):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM headlines WHERE company_id = ? AND headline = ?",
            (company_id, headline),
        ).fetchone()
        return row is not None


def insert_headline(company_id, source, headline, url, published_at, sentiment):
    if headline_exists(company_id, headline):
        return None
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO headlines
               (company_id, source, headline, url, published_at,
                sentiment_label, compound_score, pos, neu, neg, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                company_id, source, headline, url, published_at,
                sentiment["label"], sentiment["compound"],
                sentiment["pos"], sentiment["neu"], sentiment["neg"],
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def get_headlines(company_id, limit=100):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM headlines WHERE company_id = ?
               ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT ?""",
            (company_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_sentiment_summary(company_id):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT sentiment_label, COUNT(*) as cnt
               FROM headlines WHERE company_id = ?
               GROUP BY sentiment_label""",
            (company_id,),
        ).fetchall()
        summary = {"positive": 0, "neutral": 0, "negative": 0}
        for r in rows:
            summary[r["sentiment_label"]] = r["cnt"]
        return summary


def get_daily_trend(company_id, days=14):
    """Average compound sentiment score grouped by day."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT substr(COALESCE(published_at, fetched_at), 1, 10) as day,
                      AVG(compound_score) as avg_score,
                      COUNT(*) as cnt
               FROM headlines
               WHERE company_id = ?
               GROUP BY day
               ORDER BY day ASC
               LIMIT ?""",
            (company_id, days),
        ).fetchall()
        return [dict(r) for r in rows]
