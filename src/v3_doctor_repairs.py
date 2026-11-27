"""Safe on-phone Doctor repair ledger (J5). Pure logic, no I/O, no requests.

The caller (main.py) supplies the actions. This module only decides WHAT may run,
HOW OFTEN, and keeps an audit trail. It can never be asked to touch tokens, keys,
broker orders, user settings or source code: only the allowlisted, local or
already-permitted read-only actions below exist.
"""
from collections import deque
from math import isfinite

STUCK_AFTER_SECONDS = 300
MAX_ATTEMPTS_PER_GENERATION = 2
COOLDOWN_SECONDS = 120
ALLOWED_ACTIONS = ("release_busy_flag", "retry_closed_index_snapshot",
                   "retry_missing_hist", "recompute_local_cache",
                   # B243: still read-only / reconnect-only; never settings, tokens or orders
                   "reconnect_saved_ssk", "load_roster_option_chain",
                   "restart_stalled_watchlist")


def _valid_time(value):
    return type(value) in (int, float) and isfinite(value) and value >= 0


class StuckFlagWatch:
    """Remembers since when each busy flag has been continuously True."""

    def __init__(self):
        self._since = {}

    def sample(self, flags, now):
        if not _valid_time(now) or not isinstance(flags, dict):
            return
        for name, value in flags.items():
            if value is True:
                self._since.setdefault(name, now)
            else:
                self._since.pop(name, None)
        for name in [n for n in self._since if n not in flags]:
            del self._since[name]

    def stuck(self, now, limit=STUCK_AFTER_SECONDS, limits=None):
        """Names busy for at least their own limit (``limits`` overrides ``limit`` per name)."""
        if not _valid_time(now):
            return []
        limits = limits if isinstance(limits, dict) else {}
        return sorted(n for n, t in self._since.items()
                      if now - t >= limits.get(n, limit))

    def forget(self, name):
        self._since.pop(name, None)


class RepairLedger:
    CODE = "BK-DOC-REPAIR-001"

    def __init__(self):
        self._attempts = {}
        self._last = {}
        self._events = deque(maxlen=40)
        self._sequence = 0
        self._last_run = None

    def note_run(self, now, result, checked, planned=0):
        """Record every run, even when nothing was needed, so the log is never silently empty."""
        if not _valid_time(now):
            return
        self._last_run = {"at_monotonic": round(now, 1), "result": str(result)[:40],
                          "planned": int(planned) if type(planned) is int else 0,
                          "checked": [str(x)[:40] for x in (checked or ())][:20]}

    def propose(self, findings, generation, now):
        """Return only findings that are allowlisted, under the cap, and cooled down."""
        plans = []
        if type(generation) is not int or not _valid_time(now):
            return plans
        for finding in findings or ():
            if not isinstance(finding, dict):
                continue
            action = finding.get("action")
            key = (finding.get("id"), finding.get("target"))
            if action not in ALLOWED_ACTIONS or not finding.get("id"):
                continue
            if self._attempts.get((generation, key), 0) >= MAX_ATTEMPTS_PER_GENERATION:
                continue
            if now - self._last.get((generation, key), -COOLDOWN_SECONDS) < COOLDOWN_SECONDS:
                continue
            plans.append({"id": finding["id"], "action": action,
                          "target": finding.get("target"),
                          "preview": str(finding.get("preview", ""))[:200]})
        return plans

    def record(self, plan, generation, now, ok, detail=""):
        key = (plan.get("id"), plan.get("target"))
        self._attempts[(generation, key)] = self._attempts.get((generation, key), 0) + 1
        self._last[(generation, key)] = now
        self._sequence += 1
        self._events.append({"sequence": self._sequence, "code": self.CODE,
                             "id": plan.get("id"), "action": plan.get("action"),
                             "target": plan.get("target"), "generation": generation,
                             "result": "RETEST_OK" if ok else "RETEST_STILL_FAILING",
                             "detail": str(detail)[:160],
                             "tokens_touched": False, "orders_sent": 0})

    def report(self):
        return {"code": self.CODE, "events": list(self._events),
                "last_run": self._last_run,
                "allowed_actions": list(ALLOWED_ACTIONS),
                "max_attempts_per_generation": MAX_ATTEMPTS_PER_GENERATION,
                "cooldown_seconds": COOLDOWN_SECONDS,
                "provider_requests": 0, "orders_sent": 0}
