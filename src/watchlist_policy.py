"""Five-watchlist ownership and 70-equity capacity, without broker calls.

Never duplicate an equity across lists. Loaded settings are validated before
they become live state; first saved list wins, preserving the user's order.
"""
MAX_EQUITIES = 70
WATCHLIST_COUNT = 5


def normalize_watchlists(groups, *, maximum=MAX_EQUITIES):
    if not isinstance(groups, (list, tuple)) or len(groups) != WATCHLIST_COUNT:
        raise ValueError("Expected five watchlists")
    if type(maximum) is not int or maximum < 1:
        raise ValueError("Invalid watchlist capacity")
    cleaned = []
    seen = set()
    for source in groups:
        if not isinstance(source, (list, tuple)):
            source = []
        target = []
        for value in source:
            if not isinstance(value, str):
                continue
            symbol = value.strip().upper().removesuffix(".NS")
            if (not symbol or len(symbol) > 25
                    or not all(ch.isascii() and (ch.isalnum() or ch in "-&.")
                               for ch in symbol)
                    or symbol in seen or len(seen) >= maximum):
                continue
            target.append(symbol)
            seen.add(symbol)
        cleaned.append(target)
    return cleaned
