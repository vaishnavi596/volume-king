"""Mock V2 Android side for offline schema parity; NOT an APK."""
from .api_contract import parse_selection,validate_snapshot
from .gateway_contract import ContractError,INDEXES

class V2MobileFixture:
    def __init__(self):
        self.selected=()
        self.revision=-1
        self.quotes={}

    def select(self,body):
        demand=parse_selection(body)
        self.selected=demand.equities
        return len(self.selected)

    def apply(self,payload):
        p=validate_snapshot(payload)
        if p["revision"]<=self.revision:
            return False
        allowed=set(self.selected).union(INDEXES)
        if not set(p["quotes"]).issubset(allowed):
            raise ContractError("Unselected symbol in mobile feed")
        # Mirror DeviceQuoteView: a newer envelope cannot overwrite an
        # equal/older per-symbol revision, even if its price differs.
        for symbol, row in p["quotes"].items():
            previous = self.quotes.get(symbol)
            if previous is None or row["revision"] > previous["revision"]:
                self.quotes[symbol] = dict(row)
        self.revision=p["revision"]
        return True
