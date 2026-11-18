"""V2 isolated read-only data/auth *contracts*; no network or credentials."""
from dataclasses import dataclass, field
from math import isfinite

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
MAX_WATCH_EQUITIES = 70

class ContractError(ValueError):
    pass

def symbol_ok(s):
    return (type(s) is str and 1 <= len(s) <= 32 and
            all(c.isascii() and (c.isupper() or c.isdigit() or c in "&-_") for c in s))

@dataclass(frozen=True)
class Demand:
    equities: tuple
    indices: tuple = INDEXES

def plan_demand(groups):
    """Five watchlists, at most 70 unique equities; indices always independent."""
    if type(groups) not in (tuple, list) or len(groups) != 5:
        raise ContractError("Exactly five Watchlists required")
    seen = set()
    for group in groups:
        if type(group) not in (tuple, list):
            raise ContractError("Invalid Watchlist")
        for s in group:
            if not symbol_ok(s) or s in INDEXES or s in seen:
                raise ContractError("Invalid or duplicate watchlist equity")
            seen.add(s)
            if len(seen) > MAX_WATCH_EQUITIES:
                raise ContractError("70 equity capacity exceeded")
    return Demand(tuple(sorted(seen)))

@dataclass
class RevisionCache:
    """Last-good read-only cache; never manufactures verified live timestamps."""
    revision: int = -1
    rows: dict = field(default_factory=dict)

    def update(self, payload, demand):
        if type(payload) is not dict or not isinstance(demand, Demand):
            raise ContractError("Invalid snapshot")
        rev = payload.get("revision")
        quotes = payload.get("quotes")
        if (payload.get("protocol") != "botking-v2-readonly"
                or payload.get("source") != "dhan"
                or payload.get("live_orders_enabled") is not False
                or payload.get("freshness") != "unverified"
                or type(rev) is not int or rev < 0 or type(quotes) is not dict):
            raise ContractError("Untrusted gateway snapshot")
        expected = set(demand.equities + demand.indices)
        fresh = {}
        for key, val in quotes.items():
            if key not in expected or type(val) not in (int, float) or not isfinite(val) or val <= 0:
                raise ContractError("Invalid quote in snapshot")
            fresh[key] = {"price": float(val), "freshness": "unverified",
                          "live_verified": False, "revision": rev}
        if rev <= self.revision:
            return False
        self.rows.update(fresh)
        self.revision = rev
        return True

@dataclass(frozen=True)
class BrokerState:
    app_session_valid: bool
    dhan_status: str

    def __post_init__(self):
        if type(self.app_session_valid) is not bool or self.dhan_status not in (
                "CONNECTED", "REAUTH_REQUIRED", "COOLDOWN", "OFFLINE"):
            raise ContractError("Invalid authentication state")

    @property
    def data_ready(self):
        return self.app_session_valid and self.dhan_status == "CONNECTED"
