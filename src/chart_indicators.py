"""Validated chart levels and indicator summaries; no trade execution."""
import math


def chart_indicators(bars):
    clean = []
    for row in bars or []:
        try:
            if len(row) < 6:
                continue
            ts, o, h, l, c, v = [float(x or 0) for x in row[:6]]
            if not all(math.isfinite(x) for x in (ts, o, h, l, c, v)):
                continue
            if min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c) or v < 0:
                continue
            if clean and ts <= clean[-1][0]:
                continue
            clean.append((ts, o, h, l, c, v))
        except (TypeError, ValueError, OverflowError):
            continue
    if len(clean) < 30:
        return {"status": "UNAVAILABLE", "reason": "Need at least 30 ordered valid candles"}
    closes = [r[4] for r in clean]
    highs = [r[2] for r in clean]
    lows = [r[3] for r in clean]
    def ema(period):
        value = closes[0]
        for price in closes[1:]:
            value += (price - value) * (2 / (period + 1))
        return value
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = sum(max(x, 0) for x in changes[-14:]) / 14
    losses = sum(max(-x, 0) for x in changes[-14:]) / 14
    rsi = 100 if losses == 0 and gains > 0 else 50 if losses == gains == 0 else 100 - 100 / (1 + gains / losses)
    true_ranges = [highs[0] - lows[0]] + [
        max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        for i in range(1, len(clean))
    ]
    atr = true_ranges[0]
    for tr in true_ranges[1:]:
        atr = (13 * atr + tr) / 14
    # Rolling levels are not exchange-confirmed support/resistance.
    support = min(lows[-21:-1])
    resistance = max(highs[-21:-1])
    price = closes[-1]
    ema20, ema50 = ema(20), ema(50)
    bias = "BULLISH" if price > ema20 > ema50 and rsi >= 50 else (
        "BEARISH" if price < ema20 < ema50 and rsi <= 50 else "WAIT")
    return {"status": "AVAILABLE", "price": price, "ema20": ema20,
            "ema50": ema50, "rsi14": rsi, "atr14": atr,
            "support": support, "resistance": resistance,
            "bias": bias, "timestamp": clean[-1][0],
            "count": len(clean), "reason": "EMA20/50 trend and RSI14 confirmation; not a win probability"}
