"""Bounded local recovery for the Super Five observer only.

No provider, order, source-code, settings or trading-state mutation.
The existing observer performs the retry. Optional bounded disk audit is not recovery state.
"""
from collections import deque
from pathlib import Path, PurePath
import json
import os
import tempfile
import time
import traceback


class LocalObserverRecovery:
    CODE = "BK-SF-REC-001"
    FEATURE = "B2.04/SUPER_FIVE_LOCAL_OBSERVER"

    def __init__(self, journal_path=None):
        self._journal_path = Path(journal_path) if journal_path is not None else None
        self._disk_error = None
        self._persisted_sequence = 0
        self._previous = []
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
            monotonic_seconds=round(now, 3), observed_epoch=time.time(), state=state, **fields))

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

    def load_audit(self):
        """Read previous evidence only; never restore cooldown or authorize repair."""
        if self._journal_path is None:
            return
        try:
            with self._journal_path.open("rb") as handle:
                raw = handle.read(131073)
            if len(raw) > 131072:
                raise ValueError("journal size")
            document = json.loads(raw)
            if not isinstance(document, dict) or document.get("schema") != 1:
                raise ValueError("journal schema")
            rows = document.get("events")
            if not isinstance(rows, list):
                raise ValueError("journal events")
            # Disk contents are untrusted. Reconstruct only allowlisted fields.
            valid_states = {"RETRY_SCHEDULED", "ESCALATED_COOLDOWN",
                            "LOCAL_RETEST_PASS", "ABANDONED_GENERATION_CHANGED"}
            self._previous = []
            for row in rows[-40:]:
                if not isinstance(row, dict) or row.get("state") not in valid_states:
                    continue
                safe = {"state": row["state"], "code": self.CODE, "feature": self.FEATURE}
                for key in ("sequence", "generation", "observed_epoch", "monotonic_seconds",
                            "delay_seconds", "published_count"):
                    value = row.get(key)
                    if type(value) in (int, float) and abs(value) < 1e15:
                        safe[key] = value
                for key in ("stage", "error_type"):
                    value = row.get(key)
                    if isinstance(value, str) and len(value) <= 80 and value.isidentifier():
                        safe[key] = value
                location = row.get("location")
                if isinstance(location, dict):
                    safe_location = {}
                    for key in ("module", "function"):
                        value = location.get(key)
                        if isinstance(value, str) and len(value) <= 120 and all(c.isalnum() or c in "._<>" for c in value):
                            safe_location[key] = value
                    if type(location.get("line")) is int and 0 < location["line"] < 10000000:
                        safe_location["line"] = location["line"]
                    safe["location"] = safe_location
                if type(row.get("verified")) is bool:
                    safe["verified"] = row["verified"]
                self._previous.append(safe)
            self._disk_error = None
        except FileNotFoundError:
            self._disk_error = None
        except Exception as exc:
            self._disk_error = type(exc).__name__

    def audit_snapshot(self):
        """Capture immutable audit data on the observer lane before worker I/O."""
        if self._journal_path is None or self._sequence == self._persisted_sequence:
            return None
        return self._sequence, {"schema": 1, "events": (self._previous + list(self._events))[-40:]}

    def write_audit(self, document):
        """Atomic bounded app-private write; never touch market cache or settings."""
        temp = None
        try:
            self._journal_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                    dir=self._journal_path.parent, delete=False) as handle:
                temp = handle.name
                json.dump(document, handle, ensure_ascii=False, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self._journal_path)
            return None
        except Exception as exc:
            return type(exc).__name__
        finally:
            if temp is not None:
                try:
                    os.unlink(temp)
                except OSError:
                    pass

    def audit_written(self, sequence, error):
        self._disk_error = error
        if error is None:
            self._persisted_sequence = sequence

    def report(self, now):
        return dict(mode="BOUNDED_LOCAL_AUDIT" if self._journal_path is not None else "BOUNDED_SESSION_MEMORY", feature=self.FEATURE,
            generation=self._generation, pending=self._pending,
            retry_after_seconds=round(max(0.0, self._next-now), 1),
            events=list(self._events), events_total=self._sequence,
            retained_events=len(self._events), provider_requests=0, orders_sent=0,
            previous_events=list(self._previous), persisted_sequence=self._persisted_sequence,
            persistence_error=self._disk_error,
            scope="one allowlisted local observer; last 40 disk events, no other repairs")
