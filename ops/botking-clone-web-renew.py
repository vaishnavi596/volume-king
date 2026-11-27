import os
import sys
import stat
import json
import hmac
import fcntl
import hashlib
import tempfile
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path("/home/opc/botking-clone-v2-private")
TOKEN = ROOT / "dhan-token"
STATE = ROOT / "dhan-web-renewal-state.json"
PENDING = ROOT / "dhan-web-renewal-pending.json"
RECOVERY = ROOT / "dhan-web-renewal-recovery"
LOCK = ROOT / "dhan-web-renewal.lock"

IST = timezone(timedelta(hours=5, minutes=30))
API = "https://api.dhan.co/v2"
LEAD_MINUTES = 90

CLIENT = os.environ.get("DHAN_CLIENT_ID", "").strip()

# Names (never values) of the keys in the last RenewToken response, for
# diagnosis when the response cannot be understood.
LAST_RESPONSE_KEYS = []

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req, fp, code, msg, headers, newurl
    ):
        return None

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPSHandler(),
    NoRedirect()
)

def report(state, **fields):
    print(json.dumps({
        "state": state,
        "checked_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        **fields
    }), flush=True)

def secure_read(path):
    fd = os.open(
        str(path), os.O_RDONLY | os.O_NOFOLLOW
    )

    with os.fdopen(fd, "r", encoding="utf-8") as f:
        st = os.fstat(f.fileno())

        if (
            not stat.S_ISREG(st.st_mode)
            or st.st_uid != os.geteuid()
            or st.st_mode & 0o077
            or not 0 < st.st_size <= 32768
        ):
            raise ValueError("Unsafe private file")

        return f.read()

def sync_directory():
    fd = os.open(str(ROOT), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def atomic_write(path, text):
    if path.is_symlink():
        raise ValueError("Symlink rejected")

    fd, temporary = tempfile.mkstemp(
        prefix=".renewal-",
        dir=str(ROOT)
    )

    try:
        with os.fdopen(
            fd, "w", encoding="utf-8"
        ) as f:
            os.fchmod(f.fileno(), 0o600)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temporary, path)
        sync_directory()

    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def fingerprint(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

def fetch_raw(path, token, renew=False):
    headers = {
        "access-token": token,
        "Accept": "application/json"
    }

    if renew:
        headers["dhanClientId"] = CLIENT

    req = urllib.request.Request(
        API + path,
        headers=headers,
        method="GET"
    )

    with opener.open(req, timeout=20) as response:
        if response.status != 200:
            raise ValueError("Unexpected HTTP status")
        raw = response.read(100001)

    if len(raw) > 100000:
        raise ValueError("Oversized response")

    return raw

def request(path, token, renew=False):
    data = json.loads(fetch_raw(path, token, renew))

    if not isinstance(data, dict):
        raise ValueError("Invalid response")

    return data

def looks_like_token(value):
    return (
        isinstance(value, str)
        and 20 <= len(value) <= 16384
        and value.count(".") == 2
        and not any(c.isspace() for c in value)
    )

def extract_token(data, old_token):
    """Find the replacement token in a RenewToken response.

    Accepts the documented key first, then other plausible keys, and
    finally any JWT-shaped string value (one level of nesting). Returns
    None if no distinct token-shaped value exists.
    """
    LAST_RESPONSE_KEYS[:] = sorted(
        str(k)[:40] for k in data.keys()
    )[:20]

    for key in ("accessToken", "access_token", "token"):
        value = data.get(key)
        if looks_like_token(value) and value != old_token:
            return value

    nested = [data]
    for value in data.values():
        if isinstance(value, dict):
            nested.append(value)

    for container in nested:
        for value in container.values():
            if looks_like_token(value) and value != old_token:
                return value

    return None

def verify(token):
    data = request("/profile", token)

    if str(
        data.get("dhanClientId", "")
    ).strip() != CLIENT:
        raise ValueError("Account mismatch")

    if str(
        data.get("dataPlan", "")
    ).lower() != "active":
        raise ValueError("Data plan unavailable")

    expiry = datetime.strptime(
        data["tokenValidity"].strip(),
        "%d/%m/%Y %H:%M"
    ).replace(tzinfo=IST)

    if expiry <= datetime.now(timezone.utc):
        raise ValueError("Expired token")

    return expiry

def save_state(token, expiry):
    data = {
        "source": "dhan_web",
        "fingerprint": fingerprint(token),
        "expires_at": expiry.isoformat()
    }

    atomic_write(
        STATE, json.dumps(data) + "\n"
    )

def main():
    if not CLIENT:
        raise ValueError("Missing configured account")

    mode = sys.argv[1]

    if mode not in ("--init", "--tick"):
        raise ValueError("Invalid execution mode")

    if PENDING.exists() or RECOVERY.exists():
        report(
            "RECOVERY_REQUIRED",
            renewal_attempted=False
        )
        return 2

    token = secure_read(TOKEN).strip()

    if not 20 <= len(token) <= 16384:
        raise ValueError("Invalid token")

    if mode == "--init":

        if STATE.exists() or STATE.is_symlink():
            raise ValueError("State already exists")

        expiry = verify(token)

        # Exact expiry from the owner's installation
        # evidence, not an inferred 24-hour validity.
        expected = datetime.fromisoformat(
            "2026-11-27T02:11:00+05:30"
        )

        if expiry != expected:
            raise ValueError(
                "Installed token expiry mismatch"
            )

        save_state(token, expiry)

        report(
            "INITIALIZED",
            account_match=True,
            data_plan="ACTIVE",
            expiry_ist=expiry.isoformat(),
            renewal_attempted=False
        )
        return 0

    state = json.loads(secure_read(STATE))

    if state.get("source") != "dhan_web":
        raise ValueError("Unverified provenance")

    if not hmac.compare_digest(
        state.get("fingerprint", ""),
        fingerprint(token)
    ):
        report(
            "TOKEN_CHANGED_EXTERNALLY",
            renewal_attempted=False
        )
        return 2

    expiry = datetime.fromisoformat(
        state["expires_at"]
    )

    if expiry.tzinfo is None:
        raise ValueError("Invalid expiry")

    remaining = (
        expiry - datetime.now(timezone.utc)
    ).total_seconds() / 60

    if remaining <= 0:
        report(
            "EXPIRED_REAUTH_REQUIRED",
            renewal_attempted=False
        )
        return 2

    if remaining > LEAD_MINUTES:
        report(
            "NOT_DUE",
            remaining_minutes=round(remaining, 2),
            renewal_attempted=False
        )
        return 0

    confirmed_expiry = verify(token)

    if confirmed_expiry != expiry:
        raise ValueError(
            "Provider expiry differs from state"
        )

    if secure_read(TOKEN).strip() != token:
        raise ValueError("Concurrent token change")

    # Persist before sending irreversible renewal.
    # An ambiguous failure must never trigger
    # another blind rotation.
    atomic_write(PENDING, json.dumps({
        "state": "ROTATION_STARTED",
        "started_utc": datetime.now(
            timezone.utc
        ).isoformat()
    }) + "\n")

    raw = fetch_raw(
        "/RenewToken", token, renew=True
    )

    # RenewToken revokes the old token. Keep the COMPLETE raw response in
    # the private recovery file BEFORE any parsing, so a response we do not
    # understand can never lose the replacement token.
    atomic_write(
        RECOVERY,
        raw.decode("utf-8", "replace").strip() + "\n"
    )

    renewed = json.loads(raw)

    if not isinstance(renewed, dict):
        raise ValueError("Invalid renewal response")

    new_token = extract_token(renewed, token)

    if new_token is None:
        raise ValueError(
            "Renewal response has no usable token"
        )

    # Narrow the recovery file to just the replacement token.
    atomic_write(RECOVERY, new_token + "\n")

    new_expiry = verify(new_token)

    if new_expiry <= expiry:
        raise ValueError("Expiry was not extended")

    if secure_read(TOKEN).strip() != token:
        raise ValueError("Concurrent token change")

    atomic_write(TOKEN, new_token + "\n")
    save_state(new_token, new_expiry)

    RECOVERY.unlink()
    sync_directory()

    PENDING.unlink()
    sync_directory()

    report(
        "RENEWED",
        account_match=True,
        data_plan="ACTIVE",
        expiry_ist=new_expiry.isoformat(),
        gateway_restart=False,
        orders_sent=0
    )

    return 0

try:
    fd = os.open(
        str(LOCK),
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
        0o600
    )

    try:
        st = os.fstat(fd)

        if (
            not stat.S_ISREG(st.st_mode)
            or st.st_uid != os.geteuid()
            or st.st_mode & 0o077
        ):
            raise ValueError("Unsafe lock")

        fcntl.flock(
            fd,
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

        code = main()

    finally:
        os.close(fd)

except BlockingIOError:
    report("RENEWAL_ALREADY_RUNNING")
    code = 0

except Exception as e:
    report(
        "RENEWAL_BLOCKED_OR_FAILED",
        error_type=type(e).__name__,
        response_keys=list(LAST_RESPONSE_KEYS),
        recovery_required=(
            PENDING.exists() or RECOVERY.exists()
        )
    )
    code = 1

sys.exit(code)
