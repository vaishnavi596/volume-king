"""Cache-only error-only monitor for dashboard HIST agreement bars.

Observes *constructed controls*, not Flutter pixels. Keeps short in-process
history so a Scanner-then-disappear regression can be described without
continuous re-analysis, provider calls, fake candles or trading.
"""
from collections import OrderedDict

INDEXES=("NIFTY","BANKNIFTY","SENSEX")
SURFACES=("INDEX_CARDS","ANALYSIS_SLOTS")

class DashboardBarMonitor:
    def __init__(self, max_entries=160):
        self._states=OrderedDict()
        self.max_entries=max_entries

    def observe(self, *, surface, symbol, timeframe, generation,
                history_present, bar_constructed, history_count):
        if surface not in SURFACES or not isinstance(symbol,str) or not symbol:
            raise ValueError("Invalid dashboard location")
        if timeframe!="1m" or type(generation) is not int:
            raise ValueError("Expected exact 1m and provider generation")
        if type(history_present) is not bool or type(bar_constructed) is not bool:
            raise ValueError("Boolean observation required")
        if type(history_count) is not int or history_count<0:
            raise ValueError("Invalid history count")
        key=(surface,symbol,timeframe,generation)
        before=self._states.get(key) or {}
        existed=bool(before.get("last_bar_constructed"))
        shown_once=bool(before.get("ever_bar_constructed")) or bar_constructed
        code=None
        if existed and not bar_constructed:
            code=("HIST_BAR_DISAPPEARED_WITH_CACHE" if history_present
                  else "HIST_BAR_DISAPPEARED_HISTORY_MISSING")
        elif history_present and history_count>=30 and not bar_constructed:
            code="CACHED_1M_HISTORY_NO_HIST_VOTE_BAR"
        self._states[key]={"last_bar_constructed":bar_constructed,
                           "ever_bar_constructed":shown_once,
                           "history_present":history_present,
                           "history_count":history_count,
                           "code":code}
        self._states.move_to_end(key)
        while len(self._states)>self.max_entries:
            self._states.popitem(last=False)
        return code

    def report(self, *, generation, symbols=INDEXES):
        if type(generation) is not int:
            raise ValueError("Invalid generation")
        issues=[]
        grouped={}
        for key,state in self._states.items():
            surface,symbol,tf,gen=key
            if gen!=generation or symbol not in symbols:
                continue
            grouped.setdefault((symbol,tf),{})[surface]=state
            if state["code"]:
                issues.append({"code":state["code"],"symbol":symbol,
                               "timeframe":tf,"surface":surface,
                               "cached_candle_count":state["history_count"],
                               "previous_bar_was_visible_in_control_tree":
                                   state["ever_bar_constructed"],
                               "blocked_at":"HIST_VOTE_AGREEMENT_TO_DASHBOARD_CONTROL",
                               "next_action":"CHECK_SHARED_1M_HIST_SOURCE_QUALITY_AND_REBUILD"})
        for (symbol,tf),views in grouped.items():
            if all(s in views for s in SURFACES):
                a,b=(views[s]["last_bar_constructed"] for s in SURFACES)
                if a!=b:
                    issues.append({"code":"DASHBOARD_SURFACE_AGREEMENT_MISMATCH",
                                   "symbol":symbol,"timeframe":tf,
                                   "surfaces":{s:views[s]["last_bar_constructed"] for s in SURFACES},
                                   "blocked_at":"MULTIPLE_DASHBOARD_HISTORY_PRESENTERS",
                                   "next_action":"COMPARE_EXACT_FRAME_CACHE_AND_PRESENTER_ON_SAME_GENERATION"})
        return {"mode":"ERRORS_ONLY","issues":issues,"issue_count":len(issues),
                "healthy_hidden":sum(1 for s in self._states.values() if not s["code"]),
                "source":"Constructed dashboard control tree; NOT Flutter painted pixels",
                "snapshot_scope":"CURRENT_APP_PROCESS_ONLY_NOT_SERVER_MEMORY",
                "provider_requests":0,"orders_sent":0}
