"""
sentiment_analyzer.py
Classifies financial text as positive / negative / neutral.

Uses VADER (Valence Aware Dictionary and sEntiment Reasoner), a lexicon +
rule-based model that works well on short, informal text like headlines
and social posts without needing GPU/training. A small finance-specific
lexicon patch is layered on top since VADER is tuned for general/social
text and misses finance jargon (e.g. "beats estimates", "misses guidance").

Swap-in note: for higher accuracy on financial text specifically, replace
`_scores()` with a call to a finance-tuned transformer model such as
FinBERT (ProsusAI/finbert) via the `transformers` pipeline. The rest of
the app (labels: positive/neutral/negative + compound score) stays the same.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# Domain lexicon additions: finance-specific terms VADER doesn't know.
# Scores follow VADER's -4..+4 convention.
_FINANCE_LEXICON = {
    "beats": 2.5, "beat": 2.0, "beat estimates": 3.0,
    "outperform": 2.5, "outperforms": 2.5, "outperformed": 2.5, "outperforming": 2.5,
    "upgrade": 2.3, "upgraded": 2.5, "upgrades": 2.3,
    "surge": 2.8, "surges": 2.8, "surging": 2.8,
    "rally": 2.3, "rallies": 2.3, "rallying": 2.3,
    "soar": 3.0, "soars": 3.0, "soaring": 3.0,
    "record high": 2.8, "bullish": 2.5, "guidance raised": 2.8,
    "beat expectations": 2.8, "strong earnings": 2.6, "buyback": 1.5,
    "growth": 1.2, "rising demand": 1.8,
    # "demand" alone is scored mildly negative (-0.5) by VADER's general
    # lexicon (as in "he made a demand"), which misreads its neutral/
    # positive economic sense ("demand grew", "rising demand"). Zero it out.
    "demand": 0.0,
    "misses": -2.5, "miss": -2.0, "miss estimates": -3.0,
    "underperform": -2.5, "underperforms": -2.5, "underperformed": -2.5,
    "downgrade": -2.3, "downgraded": -2.5, "downgrades": -2.3,
    "plunge": -3.0, "plunges": -3.0, "plunging": -3.0,
    "slump": -2.5, "slumps": -2.5, "slumping": -2.5,
    "tumbles": -2.8, "tumble": -2.8, "tumbling": -2.8,
    "bearish": -2.5, "guidance cut": -2.8, "miss expectations": -2.8,
    "weak earnings": -2.6, "layoffs": -2.0, "lawsuit": -1.8,
    "investigation": -1.8, "bankruptcy": -3.5, "recall": -1.8,
    "fraud": -3.2, "default": -2.8,
}
_analyzer.lexicon.update(_FINANCE_LEXICON)

# VADER's standard thresholds for the compound score.
POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05


def analyze(text: str) -> dict:
    """Return sentiment scores + label for a single piece of text."""
    if not text or not text.strip():
        return {"label": "neutral", "compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= POS_THRESHOLD:
        label = "positive"
    elif compound <= NEG_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "compound": round(compound, 4),
        "pos": round(scores["pos"], 4),
        "neu": round(scores["neu"], 4),
        "neg": round(scores["neg"], 4),
    }


def analyze_batch(texts: list[str]) -> list[dict]:
    return [analyze(t) for t in texts]
