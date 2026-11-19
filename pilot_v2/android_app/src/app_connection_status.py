"""App-owned view of local V2 session readiness, with zero secret exposure.

A bearer in memory is not server authentication proof. Real P-256 login and
Oracle reachability remain unconnected to V2 main.py until device acceptance.
"""
from secure_https_reader import V2ReadonlyHTTPSReader


def local_connection_state(reader=None):
    """Strictly a diagnostic; never returns a bearer, role, or LIVE status."""
    if reader is None:
        return {"code": "NOT_CONFIGURED", "label":
                "Oracle device sign-in not configured · data WAIT", "live": False}
    if not isinstance(reader, V2ReadonlyHTTPSReader):
        raise ValueError("Invalid read-only connection handle")
    if not reader.session_active:
        return {"code": "SIGN_IN_REQUIRED", "label":
                "Device session expired/revoked · sign-in required · cached HIST retained",
                "live": False}
    return {"code": "LOCAL_BEARER_UNVERIFIED", "label":
            "In-memory session present · Oracle verification still required",
            "live": False}
