"""
sample_data.py
Generates realistic synthetic financial headlines so the dashboard can be
demoed end-to-end when live news sources are unreachable (offline dev,
sandboxed environments, rate limits). Headlines are spread across the last
14 days with a mild randomized trend so charts have something meaningful
to show, and are run through the SAME sentiment analyzer as live data.
"""

import random
from datetime import datetime, timedelta

_POSITIVE_TEMPLATES = [
    "{name} shares surge after quarterly earnings beat estimates",
    "{name} ({ticker}) hits record high on strong revenue growth",
    "Analysts upgrade {name} stock, citing bullish outlook",
    "{name} announces share buyback program, investors cheer",
    "{name} beats Wall Street expectations for Q{q} earnings",
    "{name} stock rallies on positive guidance for next quarter",
    "Investors bullish on {name} after strong product launch",
    "{name} ({ticker}) outperforms sector amid rising demand",
]

_NEGATIVE_TEMPLATES = [
    "{name} shares plunge after weak earnings report",
    "{name} ({ticker}) downgraded by analysts amid growth concerns",
    "{name} stock tumbles following disappointing guidance cut",
    "{name} faces investigation over accounting practices",
    "{name} announces layoffs as costs rise",
    "{name} ({ticker}) misses revenue expectations for Q{q}",
    "{name} stock slumps amid broader market sell-off",
    "Investors worried as {name} warns of slowing demand",
]

_NEUTRAL_TEMPLATES = [
    "{name} to report Q{q} earnings next week",
    "{name} ({ticker}) holds annual shareholder meeting",
    "{name} appoints new board member",
    "{name} stock trades flat ahead of earnings call",
    "Analysts maintain hold rating on {name} ({ticker})",
    "{name} announces date for next investor conference",
    "{name} unveils updated product roadmap",
    "Market watchers eye {name} ahead of sector data release",
]

_SOURCES = ["Reuters", "Bloomberg", "CNBC", "MarketWatch", "Yahoo Finance", "Financial Times", "Investing.com"]


def generate_headlines(company_name: str, ticker: str, count: int = 25, days_back: int = 14):
    items = []
    now = datetime.utcnow()

    # Randomized daily "mood" so the trend line looks like real market sentiment
    daily_bias = {d: random.uniform(-0.4, 0.5) for d in range(days_back)}

    for _ in range(count):
        day_offset = random.randint(0, days_back - 1)
        bias = daily_bias[day_offset]

        roll = random.random() + bias * 0.5
        if roll > 0.55:
            template = random.choice(_POSITIVE_TEMPLATES)
        elif roll < 0.30:
            template = random.choice(_NEGATIVE_TEMPLATES)
        else:
            template = random.choice(_NEUTRAL_TEMPLATES)

        headline = template.format(name=company_name, ticker=ticker, q=random.randint(1, 4))
        published = now - timedelta(days=day_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        items.append({
            "headline": headline,
            "url": None,
            "source": random.choice(_SOURCES) + " (sample)",
            "published_at": published.isoformat(),
        })

    items.sort(key=lambda x: x["published_at"], reverse=True)
    return items
