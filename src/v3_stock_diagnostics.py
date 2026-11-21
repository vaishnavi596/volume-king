"""Safe per-stock V3 diagnostic classification and recovery registry.

Read-only: never calls provider and never makes an absent candle a trade signal.
"""
from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
import math

INDEXES=("NIFTY","BANKNIFTY","SENSEX")

def _candle_fault(record,frame):
    if not isinstance(record,dict) or not record:
        return "DATA_INCOMPLETE"
    if record.get("source")!="Dhan" or record.get("_scanner_timeframe",frame)!=frame:
        return "TIMEFRAME_MISMATCH"
    bars=record.get("bars")
    if not isinstance(bars,(list,tuple)) or len(bars)<2:
        return "DATA_INCOMPLETE"
    previous=None
    for bar in bars:
        if not isinstance(bar,(tuple,list)) or len(bar)<6:
            return "CANDLE_INVALID"
        t,o,h,l,c,v=bar[:6]
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in (t,o,h,l,c,v)):
            return "CANDLE_INVALID"
        if t<=0 or (previous is not None and t<=previous) or min(o,h,l,c)<=0 or l>min(o,c) or h<max(o,c) or v<0:
            return "CANDLE_INVALID"
        previous=t
    return None

def classify_stock(symbol, quote, histories, generation):
    """Make an independent, typed, sanitized assessment for one real stock."""
    faults=[]
    p=quote.get("price") if isinstance(quote,dict) else None
    if not isinstance(quote,dict) or not quote or p is None:
        faults.append("DATA_INCOMPLETE")
    elif quote.get("source")!="Dhan" or type(p) not in (int,float) or not math.isfinite(p) or p<=0:
        faults.append("DATA_INCOMPLETE")
    for frame in ("1m","3m","5m"):
        fault=_candle_fault(histories.get((symbol,frame,generation)),frame)
        if fault:
            faults.append(fault)
    # Five option-evidence filters are deliberately not considered complete
    # without trusted expiry-scoped feed evidence. The sixth slot stays inert.
    return {"symbol":symbol,"state":"ERROR" if faults else "CACHE_PRESENT_UNVERIFIED",
            "error_codes":list(dict.fromkeys(faults)),
            "analysis_eligible":False,
            "live_signal_eligible":False,
            "cause":"; ".join(dict.fromkeys(faults)) if faults else "Data presence only; verify five filter evidence separately"}

class DiagnosticRegistry:
    """Active + bounded resolved events, isolated by provider generation."""
    def __init__(self):
        self.generation=None
        self.active={}
        self.history=deque(maxlen=100)

    def reconcile(self, results, generation):
        if self.generation!=generation:
            self.generation=generation
            self.active.clear()
            self.history.clear()
        now=datetime.now(timezone.utc).isoformat(timespec="seconds")
        seen=set()
        for result in results:
            symbol=result["symbol"]
            seen.add(symbol)
            codes=tuple(result["error_codes"])
            old=self.active.get(symbol)
            if codes:
                if old is None or old["error_codes"]!=list(codes):
                    self.active[symbol]={"symbol":symbol,"state":"ERROR","error_codes":list(codes),"since":now}
                    self.history.append({"symbol":symbol,"state":"ERROR","error_codes":list(codes),"at":now})
            elif old:
                self.active.pop(symbol,None)
                self.history.append({"symbol":symbol,"state":"RESOLVED","error_codes":old["error_codes"],"at":now})
        # Don't mark a stock resolved merely because a later smaller sample omitted it.
        return self.summary()

    def summary(self):
        return {"active_count":len(self.active),"active":list(self.active.values())[:73],
                "recent_events":list(self.history)[-20:]}
