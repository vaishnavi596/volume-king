"""Opt-in Dhan file-token selection with bounded, fail-closed verification cache.

Default compatibility behavior remains unchanged. Strict mode verifies a
file-backed token with Dhan. Cache never survives a process restart, never
outlives the verified expiry and is invalidated on file metadata changes.
"""
import os
import threading
import time
from datetime import datetime, timezone


class VerifiedTokenCache:
    def __init__(self, ttl_seconds=30, monotonic=time.monotonic):
        if not 0 < ttl_seconds <= 300:
            raise ValueError("Invalid verification cache TTL")
        self.ttl_seconds = ttl_seconds
        self.monotonic = monotonic
        self.lock = threading.RLock()
        self.entry = None

    def _fingerprint(self, path):
        stat = os.stat(path, follow_symlinks=False)
        return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)

    def verify(self, path, client_id, provider_timezone, verifier):
        with self.lock:
            try:
                fingerprint = self._fingerprint(path)
                key = (os.path.abspath(path), client_id, provider_timezone, fingerprint)
                now = datetime.now(timezone.utc)
                tick = self.monotonic()
                entry = self.entry
                if entry is not None and entry[0] == key and tick < entry[2] and now < entry[3]:
                    return entry[1]
                self.entry = None
                token, expiry = verifier(path, client_id, provider_timezone=provider_timezone)
                if not isinstance(token, str) or not token or not isinstance(expiry, datetime) or expiry.tzinfo is None:
                    return ""
                if expiry.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                    return ""
                if fingerprint != self._fingerprint(path):
                    return ""
                self.entry = (key, token, tick + self.ttl_seconds, expiry.astimezone(timezone.utc))
                return token
            except Exception:
                self.entry = None
                return ""


def select_persisted_token(path, client_id, *, strict=False, provider_timezone=None,
                           legacy_reader=None, verifier=None, cache=None):
    if strict:
        if not client_id:
            return ""
        if verifier is None:
            try:
                from .dhan_restart_validation import verify_persisted_session_with_dhan
            except ImportError:
                from dhan_restart_validation import verify_persisted_session_with_dhan
            verifier = verify_persisted_session_with_dhan
        if cache is not None:
            return cache.verify(path, client_id, provider_timezone, verifier)
        try:
            token, expiry = verifier(path, client_id, provider_timezone=provider_timezone)
            if not isinstance(expiry, datetime) or expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
                return ""
            return token if isinstance(token, str) and token else ""
        except Exception:
            return ""
    if legacy_reader is None:
        from pathlib import Path
        legacy_reader = lambda filename: Path(filename).read_text(encoding="utf-8").strip()
    try:
        return legacy_reader(path)
    except OSError:
        return ""
