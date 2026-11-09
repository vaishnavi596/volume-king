"""Explicitly opted-in, fail-closed Dhan file-token selection.

Default compatibility path is untouched by this module. Strict mode performs
a read-only profile verification before returning a file-backed token; callers
should account for up to 12 seconds of network latency per verification.
"""
def select_persisted_token(path, client_id, *, strict=False, provider_timezone=None,
                           legacy_reader=None, verifier=None):
    if strict:
        if not client_id:
            return ""
        if verifier is None:
            try:
                from .dhan_restart_validation import verify_persisted_session_with_dhan
            except ImportError:
                from dhan_restart_validation import verify_persisted_session_with_dhan
            verifier = verify_persisted_session_with_dhan
        try:
            token, _expiry = verifier(path, client_id, provider_timezone=provider_timezone)
            return token
        except Exception:
            # Never leak the token, profile response, or exception to callers.
            return ""
    if legacy_reader is None:
        from pathlib import Path
        legacy_reader = lambda filename: Path(filename).read_text(encoding="utf-8").strip()
    try:
        return legacy_reader(path)
    except OSError:
        return ""
