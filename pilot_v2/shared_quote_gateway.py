"""V2 shared server-owned read-only quote delivery, OFFLINE CONTRACT ONLY.

No Dhan HTTP/WebSocket calls: an independently authenticated upstream collector
must provide a validated snapshot. The gateway verifies each DEVICE session and
feed permission on *every* read, never accepts a client-selected role or cache.
No mutable reference to the central cache escapes via API responses.
"""
from .gateway_contract import ContractError, Demand, RevisionCache, plan_demand
from .device_sessions import DeviceSessionGateway, SessionDenied

class SharedQuoteGateway:
    def __init__(self, sessions):
        if not isinstance(sessions, DeviceSessionGateway):
            raise ValueError("Verified device session gateway required")
        self._sessions = sessions
        self._cache = RevisionCache()
        self._selections = {}

    def publish_from_trusted_collector(self, payload, union_demand):
        """Called by trusted server-internal collector, NEVER a client route.

        The caller must authenticate the collector and ensure one atomic
        publish across processes before production integration.
        """
        if not isinstance(union_demand, Demand):
            raise ContractError("Invalid union demand")
        return self._cache.update(payload, union_demand)

    def select_equities(self, session, watch_groups):
        """Device's display request, not a request to Dhan or a grant of access."""
        device = self._sessions.check_feed(session, "quotes")
        demand = plan_demand(watch_groups)
        self._selections[device] = demand.equities
        return len(demand.equities)

    def read(self, session, feed):
        if feed not in ("quotes", "indices"):
            raise SessionDenied("Unsupported shared quote feed")
        device = self._sessions.check_feed(session, feed)
        allowed = (self._selections.get(device, ())
                   if feed == "quotes" else Demand(()).indices)
        # Clone rows: consumers may mutate returned objects, never shared state.
        return {"protocol":"botking-v2-readonly",
                "revision":self._cache.revision,
                "source":"dhan",
                "freshness":"unverified",
                "live_orders_enabled":False,
                "quotes":{sym:dict(self._cache.rows[sym])
                          for sym in allowed if sym in self._cache.rows}}
