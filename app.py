"""
app.py
AI-Based Stock Market Sentiment Tracker - Flask backend.

Endpoints:
    GET  /                          -> dashboard page
    GET  /api/companies             -> list tracked companies
    POST /api/track                 -> {name, ticker} add + fetch + analyze
    GET  /api/refresh/<ticker>      -> re-fetch latest headlines for a company
    GET  /api/sentiment/<ticker>    -> summary + daily trend + headlines
"""

from flask import Flask, jsonify, request, render_template

import database
from services import news_fetcher, sentiment_analyzer, signal_generator

app = Flask(__name__)
database.init_db()


def _ingest_company(name: str, ticker: str):
    """Fetch headlines, run sentiment, persist. Returns (company_id, used_live_source)."""
    ticker = ticker.upper().strip()
    company_id = database.upsert_company(name, ticker)

    items, used_live = news_fetcher.fetch_headlines(name, ticker)
    for item in items:
        sentiment = sentiment_analyzer.analyze(item["headline"])
        database.insert_headline(
            company_id=company_id,
            source=item.get("source"),
            headline=item["headline"],
            url=item.get("url"),
            published_at=item.get("published_at"),
            sentiment=sentiment,
        )
    return company_id, used_live


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/companies", methods=["GET"])
def api_list_companies():
    return jsonify(database.list_companies())


@app.route("/api/track", methods=["POST"])
def api_track():
    payload = request.get_json(force=True, silent=True) or {}
    name = (payload.get("name") or "").strip()
    ticker = (payload.get("ticker") or "").strip()

    if not name or not ticker:
        return jsonify({"error": "Both 'name' and 'ticker' are required."}), 400

    company_id, used_live = _ingest_company(name, ticker)
    return jsonify({
        "company_id": company_id,
        "ticker": ticker.upper(),
        "live_source_used": used_live,
    })


@app.route("/api/refresh/<ticker>", methods=["GET"])
def api_refresh(ticker):
    company = database.get_company_by_ticker(ticker.upper())
    if not company:
        return jsonify({"error": "Unknown ticker. Track it first via /api/track."}), 404

    _, used_live = _ingest_company(company["name"], company["ticker"])
    return jsonify({"status": "refreshed", "live_source_used": used_live})


@app.route("/api/sentiment/<ticker>", methods=["GET"])
def api_sentiment(ticker):
    company = database.get_company_by_ticker(ticker.upper())
    if not company:
        return jsonify({"error": "Unknown ticker. Track it first via /api/track."}), 404

    headlines = database.get_headlines(company["id"], limit=100)
    summary = database.get_sentiment_summary(company["id"])
    trend = database.get_daily_trend(company["id"])

    total = sum(summary.values()) or 1
    overall_score = sum(h["compound_score"] for h in headlines) / len(headlines) if headlines else 0.0
    signal = signal_generator.generate_signal(trend, len(headlines))

    return jsonify({
        "company": company,
        "summary": summary,
        "summary_pct": {k: round(v / total * 100, 1) for k, v in summary.items()},
        "overall_score": round(overall_score, 4),
        "trend": trend,
        "headlines": headlines,
        "signal": signal,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
