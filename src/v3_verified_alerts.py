"""Foreground, cache-only alerts; no native delivery or trade authority."""
from collections import OrderedDict
from math import isfinite
from five_engine import snapshot_for_display

class VerifiedAlertGate:
    def __init__(self, capacity=256):
        self.capacity=capacity
        self.seen=OrderedDict()
        self.generation=None
        self.delivered=0
        self.delivery_errors=0
        self.last_status="UNOBSERVED"

    def candidate(self, snapshot, *, symbol, timeframe, generation, now,
                  foreground, connected, historical_mode):
        if self.generation != generation:
            self.seen.clear()
            self.generation=generation
        if not foreground or not connected or historical_mode:
            self.last_status="SUSPENDED"
            return None
        if not isinstance(symbol,str) or not symbol or timeframe not in ("1m","3m","5m"):
            self.last_status="WAIT_IDENTITY"
            return None
        if type(now) not in (int,float) or not isfinite(now) or now<=0:
            self.last_status="WAIT_TIME"
            return None
        gated=snapshot_for_display(snapshot,now=now)
        aggregate=gated["combined"]
        state=aggregate["state"]
        if state not in ("BULLISH","BEARISH"):
            self.last_status="WAIT_VERIFIED_QUORUM"
            return None
        key=(symbol,timeframe,state)
        if key in self.seen:
            self.last_status="DUPLICATE_SUPPRESSED"
            return None
        return key

    def acknowledge(self, key, *, delivered):
        if not delivered:
            self.delivery_errors+=1
            self.last_status="DELIVERY_FAILED"
            return
        # Only acknowledge after the UI accepted the alert.
        self.seen[key]=True
        while len(self.seen)>self.capacity:
            self.seen.popitem(last=False)
        self.delivered+=1
        self.last_status="FOREGROUND_DELIVERED"

    def report(self):
        return {"code":"BK-ALERT-001","scope":"selected scanner foreground only",
                "status":self.last_status,"delivered":self.delivered,
                "delivery_errors":self.delivery_errors,"native_background":"NOT_WIRED",
                "provider_requests":0,"orders_sent":0}
