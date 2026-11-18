"""V2 app-side listed-strike ATM±3 selector; does not fetch/guess Dhan data.

Requires an independently authenticated full listed strike roster + underlying
spot from the same provider observation. Returns a strict seven-row cache
payload; the UI must NEVER use arbitrary seven rows as 'ATM' without this gate.
"""
from math import isfinite
from option_evidence import OptionEvidenceError, valid_expiry

ROW_FIELDS = frozenset(("strike", "ce_price", "ce_oi", "ce_volume",
                        "pe_price", "pe_oi", "pe_volume"))


def normalized_atm_window(*, symbol, expiry, revision, observed_at,
                          spot, listed_rows, trusted_transport=False):
    if (trusted_transport is not True or type(symbol) is not str
            or not symbol or not valid_expiry(expiry)
            or type(revision) is not int or revision < 0
            or type(observed_at) is not int or observed_at <= 0
            or type(spot) not in (int, float) or not isfinite(spot)
            or spot <= 0 or type(listed_rows) is not list
            or not 7 <= len(listed_rows) <= 500):
        raise OptionEvidenceError("Complete trusted underlying and listed strikes required")
    last = 0
    for row in listed_rows:
        if type(row) is not dict or set(row) != ROW_FIELDS:
            raise OptionEvidenceError("Incomplete listed strike evidence")
        strike = row["strike"]
        if (type(strike) not in (int, float) or not isfinite(strike)
                or strike <= last):
            raise OptionEvidenceError("Listed strikes not strictly ascending")
        last = strike
        if any(type(row[k]) not in (int, float) or not isfinite(row[k])
               or row[k] < 0 for k in ROW_FIELDS - {"strike"}):
            raise OptionEvidenceError("Invalid CE/PE strike prices or interest")
    # A tie prefers lower listed strike, never an invented round-number anchor.
    anchor = min(range(len(listed_rows)), key=lambda i: (
        abs(listed_rows[i]["strike"] - spot), listed_rows[i]["strike"]))
    if anchor < 3 or anchor + 3 >= len(listed_rows):
        raise OptionEvidenceError("Seven listed ATM neighborhood strikes unavailable")
    return {"symbol": symbol, "expiry": expiry, "revision": revision,
            "observed_at": observed_at, "source": "dhan",
            "rows": [dict(r) for r in listed_rows[anchor-3:anchor+4]]}
