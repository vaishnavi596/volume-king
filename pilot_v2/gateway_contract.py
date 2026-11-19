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
    _evidenced_symbols: set = field(default_factory=set, repr=False)

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
        newly_evidenced = set()
        for key, val in quotes.items():
            if key not in expected or not symbol_ok(key):
                raise ContractError("Invalid quote in snapshot")
            if type(val) is dict:
                # New collector contract: retain its independent per-symbol
                # revision instead of stamping every row with envelope revision.
                if (set(val) != {"price", "revision"} or
                        type(val["revision"]) is not int or
                        not 0 <= val["revision"] <= rev):
                    raise ContractError("Invalid symbol revision evidence")
                price, symbol_rev = val["price"], val["revision"]
                newly_evidenced.add(key)
            else:
                # Once this symbol carries a distinct source revision, do not
                # silently downgrade it to ambiguous numeric-only evidence.
                if key in self._evidenced_symbols:
                    raise ContractError("Collector symbol revision downgrade")
                # Legacy offline numeric fixture; NOT reliable age evidence.
                price, symbol_rev = val, rev
            if (type(price) not in (int, float) or
                    not isfinite(price) or price <= 0):
                raise ContractError("Invalid quote in snapshot")
            fresh[key] = {"price": float(price), "freshness": "unverified",
                          "live_verified": False, "revision": symbol_rev}
        if rev <= self.revision:
            return False
        for key, row in fresh.items():
            previous = self.rows.get(key)
            if previous is None or row["revision"] > previous["revision"]:
                self.rows[key] = row
        self._evidenced_symbols.update(newly_evidenced)
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
