"""BOT KING V2 Dhan collector readiness — pure, no network or credentials.

An operator must supply actual Oracle/Dhan evidence; no inferred entitlement.
Rows are only provider work instructions, not actual broker API requests.
"""
from dataclasses import dataclass
from .gateway_contract import ContractError, Demand, INDEXES, symbol_ok
from .broker_token_status import DhanTokenState

EQUITY_ROUTE="dhan/ltp-batch"
INDEX_ROUTE="dhan/index-ltp-batch"

@dataclass(frozen=True)
class ProviderCapabilities:
    observed_on_oracle: bool
    authenticated: bool
    quote_equities: bool
    quote_indices: bool
    historical_candles: bool
    option_chain: bool
    renewal_supported: bool

    def __post_init__(self):
        if any(type(getattr(self,name)) is not bool for name in
               ("observed_on_oracle","authenticated","quote_equities",
                "quote_indices","historical_candles","option_chain",
                "renewal_supported")):
            raise ContractError("Invalid provider evidence flags")

@dataclass(frozen=True)
class WorkLane:
    route: str
    kind: str
    symbols: tuple

@dataclass(frozen=True)
class CollectorPlan:
    ready: bool
    reason: str
    lanes: tuple
    unverified: bool = True

def plan_collector(demand, capabilities, token):
    if not isinstance(demand,Demand) or not isinstance(
            capabilities,ProviderCapabilities) or not isinstance(token,DhanTokenState):
        raise ContractError("Invalid collector inputs")
    if (len(demand.equities)>70 or len(set(demand.equities))!=len(demand.equities)
            or any(not symbol_ok(x) or x in INDEXES for x in demand.equities)
            or demand.indices!=INDEXES):
        raise ContractError("Invalid provider demand")
    if not capabilities.observed_on_oracle:
        return CollectorPlan(False,"ORACLE_RUNTIME_UNVERIFIED",())
    if not capabilities.authenticated or not token.can_fetch:
        return CollectorPlan(False,"BROKER_AUTH_UNAVAILABLE",())
    if demand.equities and not capabilities.quote_equities:
        return CollectorPlan(False,"EQUITY_QUOTES_UNAVAILABLE",())
    if not capabilities.quote_indices:
        return CollectorPlan(False,"INDEX_QUOTES_UNAVAILABLE",())
    lanes=[]
    if demand.equities:
        lanes.append(WorkLane(EQUITY_ROUTE,"equity",tuple(sorted(demand.equities))))
    lanes.append(WorkLane(INDEX_ROUTE,"index",INDEXES))
    return CollectorPlan(True,"READY_TO_STAGE_ONLY",tuple(lanes))
