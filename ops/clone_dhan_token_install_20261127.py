#!/usr/bin/env python3
"""BOT KING Clone: install a freshly generated Dhan Web token (operator tool).

Run on Oracle as root:  sudo python3 clone_dhan_token_install_20261127.py
The token is typed/pasted at a HIDDEN prompt, never printed, never written to
any log. The old token is kept as a private backup. Only the Clone-private
files are touched; V1 (/etc/bot-king/dhan-token) is never read or changed.
No order endpoint is called. Only GET /v2/profile is used.
"""
import argparse
import fcntl
import getpass
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
API = "https://api.dhan.co/v2"
DEFAULT_ROOT = "/home/opc/botking-clone-v2-private"
DEFAULT_ENV = "/etc/bot-king/clone-v2-dhan-client.env"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_client_id(env_path):
    for line in Path(env_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("DHAN_CLIENT_ID="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if re.fullmatch(r"[A-Za-z0-9_.-]{4,64}", value):
                return value
    raise SystemExit("BLOCKED: DHAN_CLIENT_ID not found in client env file")


def profile(token):
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(), NoRedirect())
    req = urllib.request.Request(
        API + "/profile",
        headers={"access-token": token, "Accept": "application/json"},
        method="GET")
    with opener.open(req, timeout=20) as response:
        if response.status != 200:
            raise ValueError("unexpected HTTP status")
        raw = response.read(100001)
    if len(raw) > 100000:
        raise ValueError("oversized response")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("invalid response")
    return data


def verify(token, client_id, fetch=profile):
    data = fetch(token)
    if str(data.get("dhanClientId", "")).strip() != client_id:
        raise ValueError("account mismatch")
    if str(data.get("dataPlan", "")).lower() != "active":
        raise ValueError("data plan not active")
    expiry = datetime.strptime(str(data["tokenValidity"]).strip(),
                               "%d/%m/%Y %H:%M").replace(tzinfo=IST)
    return expiry


def atomic_write(root, path, text, uid, gid):
    if path.is_symlink():
        raise ValueError("symlink rejected")
    fd, temporary = tempfile.mkstemp(prefix=".install-", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            try:
                os.fchown(handle.fileno(), uid, gid)
            except PermissionError:
                pass
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        dfd = os.open(str(root), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def token_from_recovery(root):
    """Return the replacement token saved by the renewal engine (never printed)."""
    path = Path(root) / "dhan-web-renewal-recovery"
    if path.is_symlink() or not path.is_file():
        raise ValueError("no recovery file")
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    candidates = []
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict):
        stack = [data]
        while stack:
            cur = stack.pop()
            for value in cur.values():
                if isinstance(value, dict):
                    stack.append(value)
                elif isinstance(value, str):
                    candidates.append(value)
    else:
        candidates.append(text)
    good = [c for c in candidates
            if 20 <= len(c) <= 16384 and c.count(".") == 2 and not re.search(r"\s", c)]
    if len(good) != 1:
        raise ValueError("recovery file has %d token-shaped values (need 1)" % len(good))
    return good[0]


def install(root, client_id, token, now=None, fetch=profile, adopt_recovery=False):
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    if not 20 <= len(token) <= 16384 or re.search(r"\s", token):
        raise ValueError("token has invalid shape")
    st = root.stat()
    uid, gid = st.st_uid, st.st_gid
    lock = root / "dhan-web-renewal.lock"
    lfd = os.open(str(lock), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(lfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another renewal/install is running")
        recovery = root / "dhan-web-renewal-recovery"
        if (recovery.exists() or recovery.is_symlink()) and not adopt_recovery:
            raise ValueError("recovery file exists; use --adopt-recovery or review")
        pending = root / "dhan-web-renewal-pending.json"
        expiry = verify(token, client_id, fetch)
        if expiry <= now + timedelta(hours=6):
            raise ValueError("token expiry too close or already past")
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        old = root / "dhan-token"
        if old.exists() and not old.is_symlink():
            backup = root / ("dhan-token.expired-" + stamp)
            shutil.copy2(str(old), str(backup))
            os.chmod(str(backup), 0o600)
            try:
                os.chown(str(backup), uid, gid)
            except PermissionError:
                pass
        atomic_write(root, old, token + "\n", uid, gid)
        state = {"source": "dhan_web",
                 "fingerprint": hashlib.sha256(token.encode("utf-8")).hexdigest(),
                 "expires_at": expiry.isoformat()}
        atomic_write(root, root / "dhan-web-renewal-state.json",
                     json.dumps(state) + "\n", uid, gid)
        archived = None
        if pending.exists() and not pending.is_symlink():
            archived = root / ("dhan-web-renewal-pending.json.archived-" + stamp)
            os.replace(str(pending), str(archived))
        if adopt_recovery and recovery.exists() and not recovery.is_symlink():
            os.replace(str(recovery), str(root / ("dhan-web-renewal-recovery.adopted-" + stamp)))
        return {"installed": True, "expiry_ist": expiry.isoformat(),
                "pending_archived": bool(archived)}
    finally:
        os.close(lfd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--client-env", default=DEFAULT_ENV)
    parser.add_argument("--adopt-recovery", action="store_true",
                        help="use the token saved in the renewal recovery file instead of typing one")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("BLOCKED: run with sudo")
    client_id = read_client_id(args.client_env)
    try:
        if args.adopt_recovery:
            token = token_from_recovery(args.root)
        else:
            print("नया Dhan टोकन पेस्ट करें (स्क्रीन पर नहीं दिखेगा), फिर Enter:")
            token = getpass.getpass("").strip()
        result = install(args.root, client_id, token, adopt_recovery=args.adopt_recovery)
    except Exception as exc:  # never echo token-bearing text
        print("INSTALL_FAILED:", type(exc).__name__, "-", str(exc)[:120])
        print("कुछ नहीं बदला गया।")
        return 1
    print("INSTALL_OK")
    print("नई समाप्ति (IST):", result["expiry_ist"])
    print("पुराना pending अलग रखा गया:", result["pending_archived"])
    print("अगला कदम: sudo systemctl restart botking-clone-v2.service")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
