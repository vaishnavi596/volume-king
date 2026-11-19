"""V2 app-owned four-factor assessment evidence, NEVER a model prediction.

News, Futures, Options and Candle factors are separate from five source-gated
trading filters. Only an independently authenticated delivery adapter may
assert trusted_transport=True; this module itself cannot verify authentication.
No invented news, data fetch, broker order or probability percentage.
"""
from math import isfinite

FACTORS = ("news", "futures", "options", "candle")
INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
LABELS = ("News", "Futures", "Options", "Candle")

class AssessmentEvidenceError(ValueError):
    pass


class LocalAssessmentEvidence:
    def __init__(self):
        self._entries = {}

    def accept(self, symbol, revision, factor_rows, *, selected_equities=(),
               trusted_transport=False):
        selected = tuple(selected_equities)
        if (trusted_transport is not True or type(symbol) is not str
                or symbol not in INDEXES + selected
                or len(selected) > 70 or len(selected) != len(set(selected))
                or type(revision) is not int or revision < 0
                or type(factor_rows) is not dict
                or not factor_rows or not set(factor_rows).issubset(FACTORS)):
            raise AssessmentEvidenceError("Untrusted assessment context")
        valid = {}
        for key, row in factor_rows.items():
            if (type(row) is not dict
                    or set(row) != {"direction", "source", "observed_at", "eligible"}
                    or row["direction"] not in ("bullish", "bearish", "neutral")
                    or type(row["direction"]) is not str
                    or row["source"] != "dhan"
                    or row["eligible"] is not True
                    or type(row["observed_at"]) is not int
                    or row["observed_at"] <= 0):
                raise AssessmentEvidenceError("Unverified factor observation")
            valid[key] = dict(row)
        previous = self._entries.get(symbol, {})
        prior = previous.get("rows", {})
        versions = dict(previous.get("revisions", {}))
        updated = dict(prior)
        changed = False
        for key, row in valid.items():
            if revision > versions.get(key, -1) and (
                key not in prior or row["observed_at"] >= prior[key]["observed_at"]
            ):
                updated[key], versions[key], changed = row, revision, True
        if changed:
            self._entries[symbol] = {"rows": updated, "revisions": versions}
        return changed

    def rows(self, symbol, *, selected_equities=()):
        if symbol not in INDEXES + tuple(selected_equities):
            return tuple((label, "WAIT") for label in LABELS)
        evidence = self._entries.get(symbol, {}).get("rows", {})
        return tuple((label, evidence[key]["direction"].upper() + " HIST"
                      if key in evidence else "WAIT")
                     for key, label in zip(FACTORS, LABELS))

    def label(self, symbol, *, selected_equities=()):
        rows = self.rows(symbol, selected_equities=selected_equities)
        known = sum(state != "WAIT" for _, state in rows)
        return (f"Assessment · {known}/4 historical factors; "
                "not a verified live signal or win probability")

    def forget_removed(self, selected_equities):
        allowed = set(INDEXES).union(selected_equities)
        self._entries = {symbol: row for symbol, row in self._entries.items()
                         if symbol in allowed}
