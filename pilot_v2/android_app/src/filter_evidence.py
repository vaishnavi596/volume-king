"""V2 app-owned evidence-gated five-filter display, no synthetic signals."""
from math import isfinite

FILTER_KEYS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")
FILTER_LABELS = ("OI Support", "OI Resistance", "Max Pain", "PCR", "Candle Trend")
SIXTH_SLOT = ""  # Owner-reserved slot is never scored.
DIRECTIONS = ("bullish", "bearish", "neutral")

class FilterEvidenceError(ValueError):
    pass

def _validated_row(row):
    if (type(row) is not dict
            or set(row) != {"direction", "source", "observed_at", "eligible"}
            or row["direction"] not in DIRECTIONS
            or row["source"] != "dhan"
            or type(row["observed_at"]) is not int or row["observed_at"] <= 0
            or row["eligible"] is not True):
        raise FilterEvidenceError("Filter lacks trusted eligible source evidence")
    return {"direction": row["direction"], "source": "dhan",
            "observed_at": row["observed_at"], "eligible": True}

class LocalFilterEvidence:
    """Accepts fully validated source-stamped evidence, per-filter when available.

    Integration caller must independently authenticate Oracle and establish
    observation freshness. This module cannot prove Dhan provenance on its own.
    """
    def __init__(self):
        self._values = {}

    def accept(self, symbol, timeframe, revision, evidence, *,
               allowed_symbols, trusted_transport=False):
        if (trusted_transport is not True
                or type(symbol) is not str or symbol not in tuple(allowed_symbols)
                or timeframe not in ("1m", "3m", "5m")
                or type(revision) is not int or revision < 0
                or type(evidence) is not dict or set(evidence) != set(FILTER_KEYS)):
            raise FilterEvidenceError("Incomplete or untrusted five-filter snapshot")
        rows = {key: _validated_row(evidence[key]) for key in FILTER_KEYS}
        slot = (symbol, timeframe)
        previous = self._values.get(slot)
        if previous and revision <= previous["revision"]:
            return False
        self._values[slot] = {"revision": revision, "rows": rows,
                              "key_revisions": {key: revision for key in FILTER_KEYS}}
        return True

    def accept_available(self, symbol, timeframe, revision, evidence, *,
                         allowed_symbols, trusted_transport=False):
        """Independently update present eligible factors; absent factors remain WAIT.

        Uses per-factor revisions so a fast options update cannot suppress a
        slower candle update. All supplied rows validate before any mutation.
        This is NOT a signal calculation or a trusted-source attestation.
        """
        if (trusted_transport is not True or type(symbol) is not str
                or symbol not in tuple(allowed_symbols)
                or type(timeframe) is not str or timeframe not in ("1m", "3m", "5m")
                or type(revision) is not int or revision < 0
                or type(evidence) is not dict or not evidence
                or not set(evidence).issubset(FILTER_KEYS)):
            raise FilterEvidenceError("Untrusted or unsupported partial factor snapshot")
        accepted = {key: _validated_row(row) for key, row in evidence.items()}
        slot = (symbol, timeframe)
        prior = self._values.get(slot)
        previous_rows = dict(prior["rows"]) if prior else {}
        prior_revisions = dict(prior["key_revisions"]) if prior else {}
        changed = False
        for key, row in accepted.items():
            if revision > prior_revisions.get(key, -1):
                previous_rows[key] = row
                prior_revisions[key] = revision
                changed = True
        if not changed:
            return False
        self._values[slot] = {"revision": max(prior_revisions.values()),
                              "rows": previous_rows,
                              "key_revisions": prior_revisions}
        return True

    def rows(self, symbol, timeframe, *, selected_equities=()):
        if symbol not in ("NIFTY", "BANKNIFTY", "SENSEX") and symbol not in selected_equities:
            return tuple((label, "WAIT") for label in FILTER_LABELS) + (("", ""),)
        entry = self._values.get((symbol, timeframe))
        if not entry:
            return tuple((label, "WAIT") for label in FILTER_LABELS) + (("", ""),)
        return tuple(
            (label, entry["rows"][key]["direction"].upper() + " HIST"
             if key in entry["rows"] else "WAIT")
            for key, label in zip(FILTER_KEYS, FILTER_LABELS)
        ) + (("", ""),)

    def invalidate_option_factors(self, symbol):
        """Expiry change invalidates four option results, never candle trend.

        There is no safe way to reuse direction from a different expiry.
        Clearing per-factor revisions permits new evidence for the new expiry
        even if that source starts with a smaller independent revision.
        """
        if type(symbol) is not str:
            raise FilterEvidenceError("Invalid option symbol")
        for key, entry in list(self._values.items()):
            if key[0] != symbol:
                continue
            rows = dict(entry["rows"])
            versions = dict(entry["key_revisions"])
            for factor in ("oi_support", "oi_resistance", "max_pain", "pcr"):
                rows.pop(factor, None)
                versions.pop(factor, None)
            if versions:
                self._values[key] = {
                    "revision": max(versions.values()),
                    "rows": rows,
                    "key_revisions": versions,
                }
            else:
                self._values.pop(key, None)

    def forget_removed(self, selected_equities):
        allowed = set(("NIFTY", "BANKNIFTY", "SENSEX")).union(selected_equities)
        self._values = {k: v for k, v in self._values.items() if k[0] in allowed}

    def compact(self, symbol, timeframe, *, selected_equities=()):
        """One shared filter presentation for the Watchlist; no sixth score."""
        five = self.rows(symbol, timeframe, selected_equities=selected_equities)[:5]
        if all(value == "WAIT" for _, value in five):
            return f"{symbol} {timeframe} filters: WAIT (5/5 no eligible evidence)"
        return f"{symbol} {timeframe} filters: " + " · ".join(
            f"{label} {value}" for label, value in five)
