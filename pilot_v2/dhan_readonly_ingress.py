"""Fail-closed V2-only quote ingress for independently trusted Dhan transport.

This does not call Dhan, authenticate a Dhan token, or claim live freshness.
Input is *only* from a separately approved server-side producer. Never map
arbitrary HTTP client JSON to this function or rename synthetic data as live.
"""
from __future__ import annotations

import math
import time
from .api_contract import make_snapshot
from .gateway_contract import symbol_ok

INDEXES = frozenset(("NIFTY", "BANKNIFTY", "SENSEX"))
MAX_EQUITIES = 70


class IngressRejected(ValueError):
    pass


def normalize_dhan_readonly(*, feed, selected, rows, revision, observed_at,
                            now=None):
    """Validate server-internal quote rows; preserve only unverified evidence.

    Row shape: symbol -> {"price": positive finite number, "observed_at":
    positive Unix seconds}. The same timestamp is enforced on each row to
    avoid silent mixing of stale and fresh revisions. Timestamp does not by
    itself establish exchange freshness, hence live_verified is always False.
    """
    if feed not in ("indices", "quotes") or type(feed) is not str:
        raise IngressRejected("Unknown feed")
    if type(selected) not in (tuple, list):
        raise IngressRejected("Invalid selected roster")
    chosen = tuple(selected)
    if any(type(s) is not str or not symbol_ok(s) for s in chosen):
        raise IngressRejected("Invalid symbols")
    if len(chosen) != len(set(chosen)):
        raise IngressRejected("Duplicate symbols")
    if feed == "indices":
        if set(chosen) != INDEXES or len(chosen) != len(INDEXES):
            raise IngressRejected("Three independent indices required")
    else:
        if len(chosen) > MAX_EQUITIES or any(
                type(s) is not str or not symbol_ok(s) or s in INDEXES for s in chosen):
            raise IngressRejected("Invalid equity roster")
    if (type(revision) is not int or revision < 0
            or type(rows) is not dict or set(rows) != set(chosen)
            or type(observed_at) not in (int, float)
            or not math.isfinite(observed_at) or observed_at <= 0):
        raise IngressRejected("Incomplete provider snapshot")
    clock = time.time() if now is None else now
    if type(clock) not in (int, float) or not math.isfinite(clock) or clock <= 0:
        raise IngressRejected("Invalid local clock")
    # Absolute timestamps are validated for gross errors, not exchange live-ness.
    if observed_at > clock + 5 or observed_at < clock - 7 * 86400:
        raise IngressRejected("Unacceptable observation timestamp")
    quotes = {}
    for symbol in chosen:
        row = rows.get(symbol)
        if (type(row) is not dict or set(row) != {"price", "observed_at"}
                or type(row["price"]) not in (int, float)
                or not math.isfinite(row["price"]) or row["price"] <= 0
                or type(row["observed_at"]) not in (int, float)
                or not math.isfinite(row["observed_at"])
                or row["observed_at"] != observed_at):
            raise IngressRejected("Invalid or mixed-revision quote")
        quotes[symbol] = {
            "price": row["price"], "freshness": "unverified",
            "live_verified": False, "revision": revision,
        }
    return make_snapshot(revision, quotes)
