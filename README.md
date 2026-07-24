# Ledger — AI-Based Stock Market Sentiment Tracker

A working prototype for **D2-PS2**: collects financial news headlines for a
company/ticker, classifies each one as **positive / negative / neutral**,
and visualizes sentiment trends on a dashboard.

## What it does

1. **Collect** — pulls recent headlines for a company from Google News RSS
   (no API key needed).
2. **Analyze** — scores each headline with VADER sentiment analysis, layered
   with a small finance-specific lexicon (see *Why VADER* below).
3. **Store** — persists headlines + scores in SQLite so trends accumulate
   over time.
4. **Visualize** — a dashboard shows a sentiment trend line, a positive /
   neutral / negative distribution, summary counts, and a scored headline
   feed.

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**, enter a company name and ticker (e.g.
`Apple Inc.` / `AAPL`), and click **Add to desk**.

Requires Python 3.9+. Internet access is needed to pull live headlines from
Google News — if it's unreachable (offline, rate-limited, blocked), the app
automatically falls back to a synthetic sample-headline generator
(`services/sample_data.py`) so the rest of the pipeline still works and the
dashboard can be demoed end-to-end. The dashboard tells you which source was
used after each fetch.

## Project structure

```
app.py                        Flask app + REST API routes
database.py                   SQLite schema + queries (companies, headlines)
services/
  news_fetcher.py             Google News RSS fetch, with sample-data fallback
  sample_data.py               Synthetic headline generator for offline demo
  sentiment_analyzer.py        VADER + finance lexicon -> label + scores
templates/index.html          Dashboard page
static/css/style.css          Dashboard styling
static/js/dashboard.js        Dashboard logic (fetch API, render Chart.js)
data/sentiment.db             SQLite DB (created automatically on first run)
```

## API

| Method | Route                     | Description                                   |
|--------|----------------------------|------------------------------------------------|
| GET    | `/api/companies`           | List tracked companies                         |
| POST   | `/api/track`                | `{name, ticker}` → fetch, score, store          |
| GET    | `/api/refresh/<ticker>`     | Re-fetch latest headlines for a tracked company |
| GET    | `/api/sentiment/<ticker>`   | Summary counts, daily trend, scored headlines, and a buy/sell/hold signal |

## Buy / sell / hold signal

The dashboard also shows a rule-based **BUY / SELL / HOLD** signal
(`services/signal_generator.py`), generated the same way a moving-average
crossover works in technical analysis, but applied to sentiment instead of
price:

- **short-term average** = mean sentiment over the most recent ~3 tracked days
- **long-term average** = mean sentiment over the full tracked window
- if short-term is meaningfully *above* the baseline and itself positive → **BUY**
- if short-term is meaningfully *below* the baseline and itself negative → **SELL**
- otherwise → **HOLD**

A confidence score (0–100%) scales with how large that divergence is and how
much headline volume backs it.

**This is not financial advice, and the dashboard says so.** News sentiment
alone is a weak, noisy predictor of short-term price movement — it ignores
price action, volume, fundamentals, and risk management, all of which a real
strategy needs. This is built to demonstrate how a sentiment pipeline *could*
feed into a signal for a class/hackathon project, not to be traded on.

## Why VADER (and how to upgrade it)

VADER is a lexicon + rule-based sentiment model built for short, informal
text — a good fit for headlines and social posts, and it needs no GPU or
training data, which makes it a fast prototype choice. Its weakness is
finance jargon it was never tuned on (e.g. it scores the word "demand"
slightly negative, as in "he made a demand", even though "rising demand" in
a headline is neutral-to-positive). `sentiment_analyzer.py` patches VADER's
lexicon with finance-specific terms (`beats`, `downgraded`, `bearish`,
`guidance cut`, corrected `demand`, etc.) to cut down on these
misclassifications.

For higher accuracy in a production setting, swap the scoring call in
`sentiment_analyzer.py` for a finance-tuned transformer such as **FinBERT**
(`ProsusAI/finbert` via Hugging Face `transformers`). The rest of the
pipeline — storage schema, API, dashboard — doesn't need to change, since
it only expects a `{label, compound, pos, neu, neg}` dict back.

## Extending this prototype

- **More sources**: add a fetcher for X/Reddit/StockTwits posts alongside
  news headlines — same `{headline, url, source, published_at}` shape works.
- **NewsAPI.org**: swap in a keyed API for broader source coverage (stub
  noted in `news_fetcher.py`).
- **Scheduled refresh**: add a cron job or `APScheduler` job hitting
  `/api/refresh/<ticker>` every N minutes for always-fresh sentiment.
- **Price correlation**: pull daily close prices (e.g. via `yfinance`) and
  overlay them on the trend chart to visually test the "does sentiment
  predict price" hypothesis the problem statement points at.
