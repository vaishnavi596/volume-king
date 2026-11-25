"""Bounded local recovery for the Super Five observer only.

No provider, order, source-code, settings or trading-state mutation.
The existing observer performs the retry. Reports are session-memory only.
"""
from collections import deque
from math import isfinite
from pathlib import PurePath
import traceback


class LocalObserverRecovery:
    CODE = "BK-SF-REC-001"
    FEATURE = "B2.04/SUPER_FIVE_LOCAL_OBSERVER"

    def __init__(self):
        self._events = deque(maxlen=40)
        self._generation = None
        self._failures = 0
        self._next = 0.0
        self._pending = False
        self._sequence = 0

    def _event(self, state, now, **fields):
        self._sequence += 1
        self._events.append(dict(sequence=self._sequence, code=self.CODE,
            feature=self.FEATURE, generation=self._generation,
            monotonic_seconds=round(now, 3), state=state, **fields))

    def _scope(self, generation, now):
        if generation != self._generation:
            if self._pending:
                self._event("ABANDONED_GENERATION_CHANGED", now,
                    action="no further repair of old generation", verified=False)
            self._generation = generation
            self._failures = 0
            self._next = 0.0
            self._pending = False

    def ready(self, generation, now):
        self._scope(generation, now)
        return now >= self._next

    def failed(self, generation, now, exc, stage):
        self._scope(generation, now)
        self._failures += 1
        self._pending = True
        delay = (15, 30, 300)[min(self._failures - 1, 2)]
        self._next = now + delay
        frames = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
        # Only source basename/function/line, never exception message,
        # source text, arguments, absolute paths or response contents.
        location = None
        if frames:
            frame = frames[-1]
            location = dict(module=PurePath(frame.filename).name,
                            function=frame.name, line=frame.lineno)
        self._event("ESCALATED_COOLDOWN" if self._failures >= 3 else "RETRY_SCHEDULED",
            now, stage=stage, error_type=type(exc).__name__,
            location=location, delay_seconds=delay,
            action="retry existing cache-only observer after cooldown",
            verified=False, rollback="not applicable; no destructive repair",
            not_done=["provider reconnect", "cache deletion", "source change",
                      "voting override", "order execution"])
        if self._failures >= 3:
            self._failures = 0

    def succeeded(self, generation, now, published_count):
        self._scope(generation, now)
        if type(published_count) is not int or published_count <= 0:
            return
        if self._pending:
            self._event("LOCAL_RETEST_PASS", now,
                action="existing guarded ranking publication completed",
                published_count=published_count, verified=True,
                scope="local ranking publication only; not LIVE or UI acceptance")
        self._pending = False
        self._failures = 0
        self._next = 0.0

    def report(self, now):
        return dict(mode="BOUNDED_SESSION_MEMORY", feature=self.FEATURE,
            generation=self._generation, pending=self._pending,
            retry_after_seconds=round(max(0.0, self._next-now), 1),
            events=list(self._events), events_total=self._sequence,
            retained_events=len(self._events), provider_requests=0, orders_sent=0,
            scope="one allowlisted local observer; no persistent journal or other repairs")
