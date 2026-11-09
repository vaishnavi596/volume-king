"""Fail-closed, testable Dhan persisted-session status policy.

No credentials in status or errors. Verification is explicitly opt-in.
The injected verifier may make a read-only network call; production defaults off.
"""
def persisted_session_status(enabled, token_path, client_id, provider_timezone=None, verifier=None):
    if not enabled:
        return "not_checked"
    if not client_id:
        return "unverified"
    if verifier is None:
        try:
            from .dhan_restart_validation import verify_persisted_session_with_dhan
        except ImportError:
            from dhan_restart_validation import verify_persisted_session_with_dhan
        verifier = verify_persisted_session_with_dhan
    try:
        verifier(token_path, client_id, provider_timezone=provider_timezone)
    except Exception:
        # The profile body, token and exception may contain sensitive data.
        return "unverified"
    return "verified"
