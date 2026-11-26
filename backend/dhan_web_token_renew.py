"""Renew an active Dhan Web token, then atomically replace the provisioned token.

Explicit operator invocation only. No automatic activation, no order endpoints.
The current token is preserved unless the replacement token passes profile validation.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import tempfile
import stat as stat_module
import urllib.error
import urllib.request

from backend.dhan_token_expiry import parse_profile_expiry
from backend.dhan_expiry_store import save_expiry_metadata, load_expiry_metadata
from backend.dhan_renewal_policy import renewal_decision
from datetime import datetime

class RejectRenewalRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def direct_renewal_open(req, timeout):
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), RejectRenewalRedirect()
    ).open(req, timeout=timeout)

API = "https://api.dhan.co/v2"
TOKEN_FILE = Path("/etc/bot-king/dhan-token")


def request_json(url, headers, opener=direct_renewal_open):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with opener(req, timeout=20) as response:
        raw=response.read(100_001)
        if len(raw)>100_000:
            raise ValueError("Oversized Dhan renewal response")
        return json.loads(raw)


def _renew_unlocked(client_id, token_path=TOKEN_FILE, opener=direct_renewal_open, expiry_path=None, lead_minutes=90):
    if not client_id or not client_id.strip():
        raise ValueError("Client ID required")
    path = Path(token_path)
    fd=os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd,"r",encoding="utf-8") as handle:
        stat=os.fstat(handle.fileno())
        if (not stat_module.S_ISREG(stat.st_mode) or stat.st_mode & 0o077
                or stat.st_uid!=os.geteuid() or stat.st_size>16384):
            raise ValueError("Token file must be private and owner-controlled")
        old=handle.read(16385).strip()
        if len(old)>16384:
            raise ValueError("Token exceeds bounded size")
    if not old:
        raise ValueError("Token file is empty")
    recovery = path.with_name(path.name + ".recovery")
    if recovery.exists() or recovery.is_symlink():
        raise ValueError("Unresolved renewal recovery file; manual reconciliation required")
    # Recheck expiry under the rotation lock to avoid a second rotation
    # when a timer decided 'due' before another process completed renewal.
    if expiry_path is not None and Path(expiry_path).exists():
        metadata=load_expiry_metadata(expiry_path)
        decision=renewal_decision(metadata["source"],datetime.fromisoformat(metadata["expires_at"]),lead_minutes=lead_minutes)
        if decision["state"]=="valid":
            return {"status":"not_due","profile_verified":False}
        if decision["state"]!="renewal_due":
            raise ValueError("Renewal expiry or provenance no longer eligible")
    # Fail closed before a potentially irreversible remote token rotation.
    # A successful preflight cannot guarantee the later write, so recovery
    # still remains mandatory immediately after receiving the replacement.
    if not os.access(path.parent, os.W_OK | os.X_OK):
        raise ValueError("Token directory is not writable for recovery")
    probe_fd, probe_name = tempfile.mkstemp(prefix=".dhan-recovery-preflight-", dir=str(path.parent))
    try:
        os.fchmod(probe_fd, 0o600)
        with os.fdopen(probe_fd, "w", encoding="utf-8") as probe:
            probe.write("preflight\\n")
            probe.flush()
            os.fsync(probe.fileno())
        probe_fd = -1
    finally:
        if probe_fd >= 0:
            os.close(probe_fd)
        os.unlink(probe_name)
    # This call revokes the old token: never call without operator authorization.
    renewed = request_json(API + "/RenewToken",
                           {"access-token": old, "dhanClientId": client_id.strip()},
                           opener=opener)
    if not isinstance(renewed, dict):
        raise ValueError("Invalid renewal response")
    new = renewed.get("accessToken")
    if not isinstance(new, str) or len(new) < 20 or new == old:
        raise ValueError("Renewal did not return a distinct access token")
    # RenewToken revokes the previous credential. Save a private recovery copy
    # BEFORE profile verification or any further network call can fail.
    fd_recovery = os.open(str(recovery), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd_recovery, "w", encoding="utf-8") as handle:
        handle.write(new + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    profile = request_json(API + "/profile", {"access-token": new}, opener=opener)
    if not isinstance(profile, dict) or str(profile.get("dhanClientId", "")).strip() != client_id.strip():
        raise ValueError("Renewed token failed account validation; private recovery file saved")
    verified_expiry = parse_profile_expiry(profile.get("tokenValidity")) if expiry_path is not None else None
    fd, temporary = tempfile.mkstemp(prefix=".dhan-token-", dir=str(path.parent))
    try:
        os.fchmod(fd, stat.st_mode & 0o777)
        os.fchown(fd, stat.st_uid, stat.st_gid)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(new + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    if expiry_path is not None:
        save_expiry_metadata(expiry_path, verified_expiry)
    recovery.unlink()
    return {"status": "renewed", "token_saved": True, "profile_verified": True,
            "expiry_time": profile.get("tokenValidity"),
            "client_id_verified": client_id.strip()}



def renew_web_token(client_id, token_path=TOKEN_FILE, opener=direct_renewal_open, expiry_path=None, *, lead_minutes=90):
    """Serialize all cooperating renewal processes before touching Dhan."""
    path = Path(token_path)
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        lock_stat=os.fstat(fd)
        if (not stat_module.S_ISREG(lock_stat.st_mode) or lock_stat.st_mode & 0o077
                or lock_stat.st_uid!=os.geteuid()):
            raise ValueError("Renewal lock file must be private")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another token renewal is already running") from None
        return _renew_unlocked(client_id, token_path, opener, expiry_path=expiry_path,lead_minutes=lead_minutes)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description="Explicitly renew a Dhan Web token")
    parser.add_argument("--token-file", default=str(TOKEN_FILE))
    parser.add_argument("--client-id-env", default="DHAN_CLIENT_ID")
    parser.add_argument("--execute", action="store_true", help="Authorize token rotation")
    args = parser.parse_args()
    if not args.execute:
        print("DRY RUN: no token changed. Pass --execute only after review.")
        return 0
    client_id = os.environ.get(args.client_id_env, "").strip()
    try:
        result = renew_web_token(client_id, args.token_file)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print("RENEWAL FAILED:", type(exc).__name__, "(credentials hidden)")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
