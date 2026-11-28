"""Pure headline-cue helpers shared by the phone and the server runner (display context only, never a vote)."""
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import timezone

NEWS_QUERIES = {"NIFTY": "Nifty India markets", "BANKNIFTY": "Indian bank stocks", "SENSEX": "Sensex India markets"}
_POSITIVE = ("profit rises", "profit jumps", "profit surges", "raises guidance", "record profit", "wins contract",
             "upgrade", "beats estimates", "loss narrows", "rally", "rallies", "surges", "record high", "gains")
_NEGATIVE = ("profit falls", "profit drops", "cuts guidance", "fraud", "downgrade", "misses estimates", "loss widens",
             "default on", "sell-off", "selloff", "slumps", "plunges", "tumbles", "crash")


def parse_news_rss(raw, source, now):
    if len(raw) > 2_000_000 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Unsupported news XML")
    items, seen = [], set()
    for node in ET.fromstring(raw).findall("./channel/item"):
        title = " ".join((node.findtext("title") or "").split())[:350]
        try:
            stamp = parsedate_to_datetime(node.findtext("pubDate") or "")
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            ts = stamp.timestamp()
        except (TypeError, ValueError, OverflowError):
            continue
        if not title or not 0 <= now - ts <= 86400 or title.lower() in seen:
            continue
        seen.add(title.lower())
        items.append({"title": title, "published": ts, "source": (node.findtext("source") or source)[:100]})
    return sorted(items, key=lambda x: x["published"], reverse=True)[:20]


def headline_signal(items):
    """Cautious phrase cues; rumour/uncertainty words skip a headline. Not verified market impact."""
    pos = neg = 0
    for item in items or ():
        text = str(item.get("title", "")).lower()
        if re.search(r"\b(not|denies|denied|rumour|rumor|may|could)\b", text):
            continue
        up = any(t in text for t in _POSITIVE)
        down = any(t in text for t in _NEGATIVE)
        if up and not down:
            pos += 1
        elif down and not up:
            neg += 1
    bias = "POSITIVE" if pos >= 2 and neg == 0 else "NEGATIVE" if neg >= 2 and pos == 0 else "MIXED" if pos and neg else "UNCLASSIFIED"
    out = {"bias": bias, "positive": pos, "negative": neg, "n": len(items or ())}
    if pos + neg >= 2:
        out["bullish"] = round(100 * pos / (pos + neg))
        out["bearish"] = 100 - out["bullish"]
    return out
