"""Pure Dhan token status policy; NEVER logs in, renews or stores a token.

OAuth-consent may require interactive user reauthentication; a fresh Android
session cannot replace expired Dhan authorization.
"""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class DhanTokenState:
    state: str
    can_fetch: bool
    needs_user_reauth: bool

def classify_dhan_token(*, now, expires_at, renewal_supported, configured,
                        renewal_window_seconds=1800):
    fields = (now, expires_at, renewal_window_seconds)
    if (any(type(n) not in (int, float) or not isfinite(n) for n in fields)
            or now < 0 or expires_at < 0 or not 60 <= renewal_window_seconds <= 7200
            or type(renewal_supported) is not bool or type(configured) is not bool):
        raise ValueError("Invalid Dhan token status")
    if not configured:
        return DhanTokenState("NOT_CONFIGURED", False, True)
    if now >= expires_at:
        return DhanTokenState("REAUTH_REQUIRED", False, True)
    if expires_at - now <= renewal_window_seconds:
        if renewal_supported:
            return DhanTokenState("RENEWAL_DUE", True, False)
        return DhanTokenState("REAUTH_SOON", True, True)
    return DhanTokenState("CONNECTED", True, False)
