"""FT-3 Flet app local, normalized option-metrics evidence; no Dhan adapter.

This validates reported metrics. It never invents CE/PE quotes, interprets PCR
as a recommendation, or certifies source freshness/authentication itself.
"""
from math import isfinite
from datetime import date

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
FIELDS = {"symbol", "expiry", "revision", "observed_at", "source",
          "ce_oi", "pe_oi", "pcr", "max_pain", "eligible"}

class OptionEvidenceError(ValueError):
    pass

def _number(value, *, positive=False):
    return type(value) in (int, float) and isfinite(value) and (
        value > 0 if positive else value >= 0)

def valid_expiry(value):
    """Strict ISO calendar expiry; reject impossible or noncanonical dates."""
    if (type(value) is not str or len(value) != 10
            or value[4] != "-" or value[7] != "-"
            or not (value[:4] + value[5:7] + value[8:]).isascii()
            or not (value[:4] + value[5:7] + value[8:]).isdigit()):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_option_metrics(data, allowed_symbols):
    """All-or-nothing strict normalized evidence; missing feeds mean WAIT."""
    if type(data) is not dict or set(data) != FIELDS:
        raise OptionEvidenceError("Incomplete option evidence")
    if (type(allowed_symbols) not in (list, tuple, set, frozenset)
            or type(data["symbol"]) is not str
            or data["symbol"] not in allowed_symbols
            or not valid_expiry(data["expiry"])
            or type(data["revision"]) is not int or data["revision"] < 0
            or type(data["observed_at"]) is not int or data["observed_at"] <= 0
            or data["source"] != "dhan"
            or data["eligible"] is not True
            or not _number(data["ce_oi"])
            or not _number(data["pe_oi"])
            or not _number(data["pcr"])
            or not _number(data["max_pain"], positive=True)):
        raise OptionEvidenceError("Invalid option source, expiry or metrics")
    # PCR is meaningful only when there is positive CE open interest.
    if data["ce_oi"] <= 0 or abs(data["pcr"] - data["pe_oi"]/data["ce_oi"]) > max(1e-5, data["pcr"]*1e-4):
        raise OptionEvidenceError("PCR inconsistent with CE/PE interest")
    return dict(data)

class LocalOptionEvidence:
    def __init__(self):
        self._rows = {}

    def accept(self, payload, *, selected_equities=(), trusted_transport=False):
        if trusted_transport is not True:
            raise OptionEvidenceError("Authenticated transport evidence required")
        allowed = INDEXES + tuple(selected_equities)
        normalized = validate_option_metrics(payload, allowed)
        key = (normalized["symbol"], normalized["expiry"])
        old = self._rows.get(key)
        if old and normalized["revision"] <= old["revision"]:
            return False
        self._rows[key] = normalized
        return True

    def visible(self, symbol, expiry, *, selected_equities=()):
        if symbol not in INDEXES and symbol not in selected_equities:
            return {"status": "WAIT"}
        row = self._rows.get((symbol, expiry))
        if row is None:
            return {"status": "WAIT"}
        return dict(row, status="HIST")  # Timestamp alone cannot certify freshness.

    def summary(self, symbol, expiry, *, selected_equities=()):
        row = self.visible(symbol, expiry, selected_equities=selected_equities)
        if row["status"] == "WAIT":
            return f"{symbol} options: WAIT (source/expiry unavailable)"
        return f"{symbol} options {expiry}: PCR {row['pcr']:.2f} · Max Pain {row['max_pain']:,.0f} HIST"

    def forget_removed(self, selected_equities):
        allowed = set(INDEXES).union(selected_equities)
        self._rows = {key: value for key, value in self._rows.items()
                      if key[0] in allowed}

class LocalExpiryChoices:
    """App-only trusted available-expiry roster and per-symbol user selection.

    Unconfigured or empty provider responses cannot fabricate expiry choices,
    reset a last-good selection, or activate any option/filter signal.
    """
    def __init__(self):
        self._available = {}
        self._selected = {}

    def accept(self, symbol, revision, expiries, *, allowed_symbols,
               trusted_transport=False):
        if (trusted_transport is not True or type(symbol) is not str
                or symbol not in tuple(allowed_symbols)
                or type(revision) is not int or revision < 0
                or type(expiries) is not list or not 1 <= len(expiries) <= 64
                or any(not valid_expiry(x) for x in expiries)
                or len(expiries) != len(set(expiries))
                or expiries != sorted(expiries)):
            raise OptionEvidenceError("Untrusted or invalid Dhan expiry roster")
        previous = self._available.get(symbol)
        if previous and revision <= previous["revision"]:
            return False
        accepted = tuple(expiries)
        self._available[symbol] = {"revision": revision, "expiries": accepted}
        if self._selected.get(symbol) not in accepted:
            self._selected.pop(symbol, None)
        return True

    def available(self, symbol, *, selected_equities=()):
        if symbol not in INDEXES and symbol not in selected_equities:
            return ()
        row = self._available.get(symbol)
        return row["expiries"] if row else ()

    def choose(self, symbol, expiry, *, selected_equities=()):
        if expiry not in self.available(symbol, selected_equities=selected_equities):
            raise OptionEvidenceError("Expiry not verified for selected symbol")
        self._selected[symbol] = expiry

    def selected(self, symbol, *, selected_equities=()):
        available = self.available(symbol, selected_equities=selected_equities)
        chosen = self._selected.get(symbol)
        return chosen if chosen in available else None

    def forget_removed(self, selected_equities):
        allowed = set(INDEXES).union(selected_equities)
        self._available = {s: row for s, row in self._available.items()
                           if s in allowed}
        self._selected = {s: value for s, value in self._selected.items()
                          if s in allowed}
