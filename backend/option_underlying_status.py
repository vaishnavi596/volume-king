"""Fail-closed, request-free PCR underlying diagnostics for BOT KING.

An equity cash-market mapping is NOT evidence of listed derivatives or
permission to request Dhan option chains. This helper never calls a broker.
"""
import re

_ALLOWED_SEGMENTS = frozenset(("IDX_I", "BSE_I", "NSE_EQ"))


def option_underlying_status(symbol, instruments):
    """Return only instrument mapping information, not a market availability claim.

    Safe to call across a watchlist because it performs zero network requests.
    """
    if (not isinstance(symbol, str)
            or not re.fullmatch(r"[A-Z0-9&_-]{1,32}", symbol)):
        return {"symbol": None, "status": "invalid_symbol",
                "mapped": False, "expiry_verified": False,
                "chain_verified": False, "pcr_verified": False,
                "broker_requests": 0}
    item = instruments.get(symbol) if isinstance(instruments, dict) else None
    mapped = bool(isinstance(item, (tuple, list)) and len(item) == 3
                  and item[0] in _ALLOWED_SEGMENTS
                  and type(item[1]) is int and item[1] > 0
                  and item[2] in ("INDEX", "EQUITY"))
    return {"symbol": symbol, "status": "mapping_only" if mapped else "unmapped",
            "mapped": mapped, "expiry_verified": False,
            "chain_verified": False, "pcr_verified": False,
            "broker_requests": 0}


def summarize_underlyings(symbols, instruments):
    """Bounded summary of a set of names, never an implicit chain scan."""
    if (not isinstance(symbols, (list, tuple)) or len(symbols) > 70
            or len(symbols) != len(set(symbols))):
        raise ValueError("Invalid or excessive underlying selection")
    rows = [option_underlying_status(s, instruments) for s in symbols]
    return {"total": len(rows), "mapped_cash_or_index": sum(r["mapped"] for r in rows),
            "broker_listed_expiry_verified": 0,
            "broker_option_chain_verified": 0,
            "broker_pcr_verified": 0,
            "network_requests": 0, "rows": rows}
