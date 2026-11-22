"""Clone B2 focus roster: never poll every inactive page's assessment.

Pure local selection helper. This is NOT an exchange risk stop or quote broker loop.
Caller still applies its existing data-source, quota and session checks.
"""


def focused_contexts(page, *, indices, scanner=None, option=None,
                     chart=None, watch=None, trading=()):
    contexts = []
    # Page indexes are the existing Clone navigation mapping.
    if page == 0:  # Dashboard/Super Five
        contexts.extend(("overview", sym) for sym in indices)
    elif page == 1 and option:
        contexts.append(("options", option))
    elif page == 3 and scanner:
        contexts.append(("scanner", scanner))
    elif page == 4 and watch:
        contexts.append(("watchlist", watch))
    elif page == 5 and chart:
        contexts.append(("chart", chart))
    # Preserve independent position evidence even when an unrelated page opens.
    for sym in trading:
        contexts.append(("overview", sym))
    # One logical context per surface/symbol, preserving active priority.
    result, seen = [], set()
    for surface, sym in contexts:
        if isinstance(sym, str) and sym and (surface, sym) not in seen:
            result.append((surface, sym))
            seen.add((surface, sym))
    return result


def priority_equity_batch(watch_symbols, position_symbols, *, verified, limit=70):
    """One deduplicated <=70 equity roster; open paper positions first.

    A reserved position can displace a watch-only quote when the combined
    selection exceeds Dhan's maximum. All names must be registry verified;
    index quotes use their separate existing lane.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Invalid equity request budget")
    permitted = set(verified) - {"NIFTY", "BANKNIFTY", "SENSEX"}
    result, seen = [], set()
    for symbol in tuple(position_symbols) + tuple(watch_symbols):
        if symbol in permitted and symbol not in seen:
            seen.add(symbol)
            result.append(symbol)
            if len(result) >= limit:
                break
    return result


def auto_equity_quote_due(now, previous_attempt, *, busy=False, floor_seconds=60):
    """True only when a shared equity request can begin; not a UI render clock.

    A backward clock jump fails closed. The initial login (no attempt) is due.
    Provider-specific cooldowns remain the caller's separate mandatory gate.
    """
    if busy or not isinstance(now,(int,float)) or isinstance(now,bool):
        return False
    if not isinstance(floor_seconds,(int,float)) or floor_seconds<60:
        return False
    if not isinstance(previous_attempt,(int,float)) or isinstance(previous_attempt,bool):
        return False
    if previous_attempt<=0:
        return now>=0
    return now>=previous_attempt and now-previous_attempt>=floor_seconds


def active_quote_view(page):
    """Return only the mounted quote-consuming page; never refresh hidden pages."""
    return page if page in (0,3,4) else None
