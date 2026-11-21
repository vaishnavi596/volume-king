"""BOT KING V3 read-only live Building Doctor and adaptive UI pacing.

No broker requests. Presence is not proof of completed/live data or raster paint.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
import math
import time

FRAMES=("1m","3m","5m")
INDICES=("NIFTY","BANKNIFTY","SENSEX")

@dataclass
class BuildingDoctor:
    started: float=field(default_factory=time.monotonic)
    counters: dict=field(default_factory=lambda: {"page_updates":0,"mounted_refreshes":0,"unchanged_skips":0})
    samples: dict=field(default_factory=dict)
    error_types: deque=field(default_factory=lambda: deque(maxlen=12))
    login_clock: float | None=None
    milestones: dict=field(default_factory=dict)

    def start_login(self):
        self.login_clock=time.monotonic()
        self.milestones={"login_clicked_s":0.0}

    def milestone(self,name):
        if self.login_clock is not None:
            self.milestones[name]=round(time.monotonic()-self.login_clock,3)

    def observe(self,name,duration_ms):
        if type(duration_ms) not in (float,int) or not math.isfinite(duration_ms) or duration_ms<0:return
        self.samples.setdefault(name,deque(maxlen=60)).append(round(duration_ms,3))

    def error(self,area,kind):
        self.error_types.append((str(area)[:48],str(kind)[:48]))

    def adaptive_gap(self,screen):
        """Only pace UI; never modify broker refresh or candle timeframes."""
        readings=self.samples.get("mounted_refresh_ms") or ()
        if not readings:return .25
        ordered=sorted(readings)
        p90=ordered[min(len(ordered)-1,int((len(ordered)-1)*.9))]
        return round(max(.10,min(1.5,p90*(3 if screen=="dashboard" else 2)/1000)),3)

    @staticmethod
    def valid_quote(row):
        p=row.get("price") if isinstance(row,dict) else None
        return type(p) in (int,float) and math.isfinite(p) and p>0 and row.get("source")=="Dhan"

    @staticmethod
    def valid_history(row,tf):
        if not isinstance(row,dict) or row.get("source")!="Dhan" or row.get("_scanner_timeframe",tf)!=tf:return False
        bars=row.get("bars")
        return isinstance(bars,list) and len(bars)>=2

    def report(self,symbols,quotes,histories,generation,connected=False):
        names=tuple(dict.fromkeys((*INDICES,*(s for s in symbols if isinstance(s,str)))))
        q=sum(bool(self.valid_quote(quotes.get(s))) for s in names)
        frames={tf:sum(bool(self.valid_history(histories.get((s,tf,generation)),tf)) for s in names) for tf in FRAMES}
        full=bool(names) and q==len(names) and all(n==len(names) for n in frames.values())
        timings={k:{"last_ms":v[-1],"max_ms":max(v),"avg_ms":round(sum(v)/len(v),3),"samples":len(v)} for k,v in self.samples.items() if v}
        return {"state":"FULL_STOCK_OBSERVED_UNVERIFIED" if full else "PARTIAL_WAIT",
                "connected":bool(connected),"instruments":len(names),"dhan_quote_present":q,
                "candle_presence_by_frame":frames,"cache_complete_presence":full,
                "source_quality_verified_live":False,
                "elapsed_session_s":round(time.monotonic()-self.started,2),
                "refresh_gap_dashboard_s":self.adaptive_gap("dashboard"),
                "refresh_gap_scanner_s":self.adaptive_gap("scanner"),
                "counters":dict(self.counters),"timings":timings,"login_milestones_seconds":dict(self.milestones),
                "errors":list(self.error_types),
                "disclaimer":"Cache presence only; not full exchange-verified candles, live five-filter score, network arrival duration or Flutter pixels."}
