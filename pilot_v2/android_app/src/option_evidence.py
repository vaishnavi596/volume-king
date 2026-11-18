"""FT-3 Flet app local, normalized option-metrics evidence; no Dhan adapter.

This validates reported metrics. It never invents CE/PE quotes, interprets PCR
as a recommendation, or certifies source freshness/authentication itself.
"""
from math import isfinite

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
FIELDS = {"symbol", "expiry", "revision", "observed_at", "source",
          "ce_oi", "pe_oi", "pcr", "max_pain", "eligible"}

class OptionEvidenceError(ValueError):
    pass

def _number(value, *, positive=False):
    return type(value) in (int, float) and isfinite(value) and (
        value > 0 if positive else value >= 0)

def validate_option_metrics(data, allowed_symbols):
    """All-or-nothing strict normalized evidence; missing feeds mean WAIT."""
    if type(data) is not dict or set(data) != FIELDS:
        raise OptionEvidenceError("Incomplete option evidence")
    if (type(allowed_symbols) not in (list, tuple, set, frozenset)
            or type(data["symbol"]) is not str
            or data["symbol"] not in allowed_symbols
            or type(data["expiry"]) is not str
            or len(data["expiry"]) != 10
            or data["expiry"][4] != "-" or data["expiry"][7] != "-"
            or not (data["expiry"][:4] + data["expiry"][5:7] +
                    data["expiry"][8:]).isdigit()
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
