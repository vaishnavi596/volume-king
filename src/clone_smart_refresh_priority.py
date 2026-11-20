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
