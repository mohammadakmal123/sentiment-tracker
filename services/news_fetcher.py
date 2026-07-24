"""
news_fetcher.py
Pulls recent financial headlines for a company/ticker.

Primary source: Google News RSS (no API key required). This is a live web
request, so it needs outbound internet access at runtime.

Fallback: If the network call fails (offline sandbox, blocked egress, rate
limit, etc.) we fall back to services.sample_data, which generates
realistic synthetic headlines so the rest of the pipeline (sentiment
scoring, storage, dashboard) can still be demoed end-to-end.

Swap-in note: to use NewsAPI.org instead, sign up for a free key and
replace `_fetch_google_news_rss()` with a call to
https://newsapi.org/v2/everything?q=<company>&apiKey=<key>
"""

import feedparser
import requests
from urllib.parse import quote_plus
from datetime import datetime

from services import sample_data

USER_AGENT = "Mozilla/5.0 (SentimentTracker/1.0)"
# (connect_timeout, read_timeout) — explicit tuple so a hung DNS lookup or
# a stalled connection can't block the request indefinitely.
TIMEOUT_SECONDS = (5, 8)


def _fetch_google_news_rss(query: str, max_items: int = 25):
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}+stock&hl=en-US&gl=US&ceid=US:en"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    items = []
    for entry in feed.entries[:max_items]:
        published = None
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6]).isoformat()
        source = entry.get("source", {}).get("title") if isinstance(entry.get("source"), dict) else "Google News"
        items.append({
            "headline": entry.get("title", "").strip(),
            "url": entry.get("link"),
            "source": source or "Google News",
            "published_at": published,
        })
    return items


def fetch_headlines(company_name: str, ticker: str, max_items: int = 25):
    """
    Returns (items, used_live_source: bool)
    items: list of {headline, url, source, published_at}
    """
    query = f"{company_name} {ticker}".strip()
    try:
        items = _fetch_google_news_rss(query, max_items=max_items)
        if items:
            return items, True
        raise ValueError("Empty feed (no articles returned)")
    except Exception as exc:
        # Network unavailable, feed empty, or blocked -> synthetic fallback.
        # Printed to the console (not the browser) so it's easy to diagnose
        # why live fetching failed on this machine/network.
        print(f"[news_fetcher] Live fetch failed for '{query}': {type(exc).__name__}: {exc}")
        print("[news_fetcher] Falling back to sample data.")
        items = sample_data.generate_headlines(company_name, ticker, count=max_items)
        return items, False
