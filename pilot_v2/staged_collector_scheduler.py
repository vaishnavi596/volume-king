"""S1 offline bridge: readiness gate before a durable quote work lease.

This module never calls the broker. It is not a live collector or approval
to run provider queries; operator-observed capabilities must be supplied.
All concurrent request budgets are delegated to one local SQLite gate.
"""
from dataclasses import dataclass
from .collector_readiness import plan_collector, CollectorPlan
from .durable_quote_gate import DurableQuoteGate, DurableLease
from .gateway_contract import ContractError, Demand
from .broker_token_status import DhanTokenState
from .collector_readiness import ProviderCapabilities

@dataclass(frozen=True)
class StagedWork:
    readiness: CollectorPlan
    lease: DurableLease | None
    lanes: tuple

class StagedCollectorScheduler:
    def __init__(self, gate):
        if not isinstance(gate, DurableQuoteGate):
            raise ValueError("Durable quote gate required")
        self._gate=gate

    def acquire(self, demand, capabilities, token):
        readiness=plan_collector(demand,capabilities,token)
        if not readiness.ready:
            return StagedWork(readiness,None,())
        lease=self._gate.begin(demand)
        if lease is None:
            return StagedWork(readiness,None,())
        eligible=set(lease.symbols)
        lanes=tuple(type(lane)(lane.route,lane.kind,
                    tuple(x for x in lane.symbols if x in eligible))
                    for lane in readiness.lanes)
        lanes=tuple(lane for lane in lanes if lane.symbols)
        # One durable lease is the unit of budgeted work, even when
        # separate equity/index endpoints are needed.
        if not lanes:
            self._gate.complete(lease)
            raise ContractError("Empty budgeted lane plan")
        return StagedWork(readiness,lease,lanes)

    def finish(self, work, *, provider_429_retry_after=None):
        if not isinstance(work,StagedWork) or work.lease is None:
            raise ContractError("No active work lease")
        self._gate.complete(work.lease,retry_after=provider_429_retry_after)
