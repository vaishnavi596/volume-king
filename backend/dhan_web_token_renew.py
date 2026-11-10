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
import urllib.error
import urllib.request

API = "https://api.dhan.co/v2"
TOKEN_FILE = Path("/etc/bot-king/dhan-token")


def request_json(url, headers, opener=urllib.request.urlopen):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with opener(req, timeout=20) as response:
        return json.loads(response.read(100_000))


def _renew_unlocked(client_id, token_path=TOKEN_FILE, opener=urllib.request.urlopen):
    if not client_id or not client_id.strip():
        raise ValueError("Client ID required")
    path = Path(token_path)
    stat = path.stat()
    if not path.is_file() or stat.st_mode & 0o077:
        raise ValueError("Token file must be private")
    old = path.read_text(encoding="utf-8").strip()
    if not old:
        raise ValueError("Token file is empty")
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
    recovery = path.with_name(path.name + ".recovery")
    fd_recovery = os.open(str(recovery), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd_recovery, "w", encoding="utf-8") as handle:
        handle.write(new + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    profile = request_json(API + "/profile", {"access-token": new}, opener=opener)
    if not isinstance(profile, dict) or str(profile.get("dhanClientId", "")).strip() != client_id.strip():
        raise ValueError("Renewed token failed account validation; private recovery file saved")
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
    recovery.unlink()
    return {"status": "renewed", "token_saved": True, "profile_verified": True,
            "expiry_time": profile.get("tokenValidity"),
            "client_id_verified": client_id.strip()}



def renew_web_token(client_id, token_path=TOKEN_FILE, opener=urllib.request.urlopen):
    """Serialize all cooperating renewal processes before touching Dhan."""
    path = Path(token_path)
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if os.fstat(fd).st_mode & 0o077:
            raise ValueError("Renewal lock file must be private")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another token renewal is already running") from None
        return _renew_unlocked(client_id, token_path, opener)
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
