"""Isolated Day-2 bounded apply-queue prototype. NO broker, UI, or server access.

This module is intentionally not imported by production src/main.py.
It exercises the phone-side receive -> stage -> apply policy with fake data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import OrderedDict
from typing import Any


PRIORITY = {
    "dashboard": 0,
    "watchlist": 1,
    "scanner": 2,
    "super_five": 3,
    "options": 4,
    "chart": 5,
    "other": 6,
}


@dataclass(frozen=True)
class Update:
    section: str
    symbol: str
    kind: str
    revision: int
    value: Any
    timeframe: str = ""
    expiry: str = ""
    completed: bool = False


@dataclass
class ApplyReport:
    applied: list[Update] = field(default_factory=list)
    deferred: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)
    queue_length: int = 0


class SmartApplyQueue:
    """Bounded, coalescing, no-network fake mobile update queue.

    A UI integrator must call apply_tick with its measured frame budget and
    must make the actual mounted-control update outside this module.
    """

    def __init__(self, max_pending: int = 512) -> None:
        if max_pending < 1:
            raise ValueError("max_pending must be positive")
        self.max_pending = max_pending
        self.pending: OrderedDict[tuple[str, str, str, str, str], Update] = OrderedDict()
        self.applied_revisions: dict[tuple[str, str, str, str, str], int] = {}
        self.diagnostics: list[dict[str, str]] = []
        self.counts = {"received": 0, "queued": 0, "applied": 0,
                       "superseded": 0, "stale_ignored": 0,
                       "capacity_rejected": 0, "failed": 0}

    @staticmethod
    def key(update: Update) -> tuple[str, str, str, str, str]:
        return (update.section, update.symbol, update.kind,
                update.timeframe, update.expiry)

    def receive(self, update: Update) -> bool:
        self.counts["received"] += 1
        if not isinstance(update, Update) or type(update.revision) is not int or update.revision < 0:
            self._problem("INVALID_UPDATE", "Invalid update/revision")
            return False
        if update.section not in PRIORITY or not update.symbol or not update.kind:
            self._problem("INVALID_KEY", "Missing section/symbol/kind")
            return False
        if update.kind == "candle" and not update.timeframe:
            self._problem("INVALID_TIMEFRAME", "Candle timeframe required")
            return False
        key = self.key(update)
        previous = self.pending.get(key)
        last = self.applied_revisions.get(key, -1)
        if update.revision <= max(last, previous.revision if previous else -1):
            self.counts["stale_ignored"] += 1
            return False
        if previous is not None:
            self.counts["superseded"] += 1
        elif len(self.pending) >= self.max_pending:
            self.counts["capacity_rejected"] += 1
            self._problem("QUEUE_CAPACITY", "Queue full; retain last-good and slow producer")
            return False
        self.pending[key] = update
        self.counts["queued"] += 1
        return True

    def apply_tick(self, max_items: int, apply=None) -> ApplyReport:
        """Apply no more than max_items. The caller sets count from real UI timing.

        A failed callback is retried later, not silently marked as applied.
        """
        if max_items < 0:
            raise ValueError("negative budget")
        result = ApplyReport()
        # Stable priority in O(n log n), not repeated O(n) index lookups.
        # Insertion order breaks ties, preventing needless queue churn.
        keys = sorted(self.pending, key=lambda k: PRIORITY[k[0]])
        for key in keys[:max_items]:
            update = self.pending[key]
            try:
                if apply is not None:
                    apply(update)
            except Exception as exc:
                self.counts["failed"] += 1
                code = "APPLY_FAILED"
                self._problem(code, type(exc).__name__)
                result.errors.append({"code": code, "section": update.section,
                                      "symbol": update.symbol,
                                      "reason": type(exc).__name__})
                # Failed item remains buffered, allowing explicit retry/diagnosis.
                continue
            self.applied_revisions[key] = update.revision
            del self.pending[key]
            self.counts["applied"] += 1
            result.applied.append(update)
        result.queue_length = len(self.pending)
        result.deferred = len(self.pending)
        return result

    def health(self) -> dict[str, Any]:
        return {"counts": dict(self.counts), "pending": len(self.pending),
                "issues": list(self.diagnostics[-20:]),
                "state": "DEGRADED" if self.counts["failed"] or self.counts["capacity_rejected"] else "OK"}

    def _problem(self, code: str, reason: str) -> None:
        self.diagnostics.append({"code": code, "reason": reason})
        if len(self.diagnostics) > 100:
            del self.diagnostics[:-100]
