"""
signal_generator.py
Produces an educational BUY / SELL / HOLD signal from sentiment trend data.

Approach: sentiment-momentum crossover — the same idea as a moving-average
crossover in technical analysis, applied to daily average sentiment score
instead of price.

    short_avg = average sentiment over the most recent few days
    long_avg  = average sentiment over the full tracked window

If short-term sentiment is meaningfully above the longer-term baseline AND
recently positive -> BUY. If meaningfully below AND recently negative ->
SELL. Otherwise -> HOLD. Confidence scales with how large that divergence
is and how much headline volume backs it (more headlines = more signal,
less noise).

IMPORTANT — Educational limitation, not financial advice:
News-sentiment alone is a weak, noisy predictor of short-term price moves.
This module exists to demonstrate how a sentiment pipeline *could* feed a
trading signal, for a class/hackathon project — it intentionally does not
use price data, volume, fundamentals, or risk management, all of which a
real strategy needs. Treat its output as a talking point, not a trade
instruction.
"""

MOMENTUM_THRESHOLD = 0.10   # how far short-term must diverge from long-term
STRONG_SCORE_THRESHOLD = 0.05  # how positive/negative recent sentiment itself must be
FULL_CONFIDENCE_HEADLINES = 20  # headline count considered "plenty of data"


def generate_signal(trend: list[dict], headline_count: int) -> dict:
    """
    trend: list of {day, avg_score, cnt} ordered oldest -> newest
           (as returned by database.get_daily_trend)
    headline_count: total number of headlines behind this trend
    """
    if not trend or len(trend) < 2:
        return {
            "signal": "HOLD",
            "confidence": 0.0,
            "short_avg": 0.0,
            "long_avg": 0.0,
            "momentum": 0.0,
            "reasoning": [
                "Not enough daily history yet to compare short-term vs "
                "longer-term sentiment. Track this company for a few more "
                "days, or refresh to pull more headlines."
            ],
        }

    scores = [t["avg_score"] for t in trend]

    short_n = min(3, len(scores))
    short_avg = sum(scores[-short_n:]) / short_n
    long_avg = sum(scores) / len(scores)
    momentum = short_avg - long_avg

    reasoning = [
        f"Short-term sentiment (last {short_n} day{'s' if short_n != 1 else ''} "
        f"tracked): {short_avg:+.2f}",
        f"Longer-term baseline (last {len(scores)} days tracked): {long_avg:+.2f}",
        f"Momentum (short-term minus baseline): {momentum:+.2f}",
    ]

    if momentum > MOMENTUM_THRESHOLD and short_avg > STRONG_SCORE_THRESHOLD:
        signal = "BUY"
        reasoning.append(
            "Recent sentiment is both positive and rising faster than the "
            "longer-term baseline — momentum is turning favorable."
        )
    elif momentum < -MOMENTUM_THRESHOLD and short_avg < -STRONG_SCORE_THRESHOLD:
        signal = "SELL"
        reasoning.append(
            "Recent sentiment is both negative and falling faster than the "
            "longer-term baseline — momentum is turning unfavorable."
        )
    else:
        signal = "HOLD"
        reasoning.append(
            "No clear sentiment momentum in either direction relative to "
            "the baseline."
        )

    data_factor = min(headline_count / FULL_CONFIDENCE_HEADLINES, 1.0)
    magnitude_factor = min(abs(momentum) / 0.3, 1.0)

    if signal == "HOLD":
        confidence = round(0.25 * data_factor, 2)
    else:
        confidence = round(0.5 * data_factor + 0.5 * magnitude_factor, 2)

    return {
        "signal": signal,
        "confidence": confidence,
        "short_avg": round(short_avg, 3),
        "long_avg": round(long_avg, 3),
        "momentum": round(momentum, 3),
        "reasoning": reasoning,
    }
