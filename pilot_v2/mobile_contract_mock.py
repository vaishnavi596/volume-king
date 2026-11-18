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
        self.quotes.update({k:dict(v) for k,v in p["quotes"].items()})
        self.revision=p["revision"]
        return True
