"""Atomic owner-private persistence for verified Dhan expiry metadata.

No access token is written to this file. The caller must supply an expiry
parsed from a verified Dhan profile response.
"""
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone


def save_expiry_metadata(path, expiry_utc, source="dhan_web"):
    if source != "dhan_web":
        raise ValueError("Only verified Dhan Web expiry can be persisted")
    try:
        parsed = datetime.fromisoformat(expiry_utc)
    except (TypeError, ValueError):
        raise ValueError("Invalid expiry timestamp") from None
    if parsed.tzinfo is None or parsed.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        raise ValueError("Expiry must be future and timezone-aware")
    target = Path(path)
    if not target.parent.is_dir():
        raise ValueError("Metadata directory missing")
    if target.is_symlink():
        raise ValueError("Metadata symlink rejected")
    if target.exists():
        st = target.stat()
        if not target.is_file() or st.st_mode & 0o077 or st.st_uid != os.geteuid():
            raise ValueError("Existing metadata must be owner-private")
    payload = {"source": source, "expires_at": parsed.astimezone(timezone.utc).isoformat()}
    fd, temporary = tempfile.mkstemp(prefix=".dhan-expiry-", dir=str(target.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(str(target.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"saved": True, "expires_at": payload["expires_at"]}

def load_expiry_metadata(path):
    """Read only trusted, owner-private metadata; never infer provenance."""
    target = Path(path)
    if target.is_symlink() or not target.is_file():
        raise ValueError("Expiry metadata must be a regular file")
    st = target.stat()
    if st.st_mode & 0o077 or st.st_uid != os.geteuid():
        raise ValueError("Expiry metadata must be owner-private")
    with target.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or set(data) != {"source", "expires_at"}:
        raise ValueError("Unexpected expiry metadata")
    if data["source"] != "dhan_web":
        raise ValueError("Unverified expiry provenance")
    try:
        expiry = datetime.fromisoformat(data["expires_at"])
    except (TypeError, ValueError):
        raise ValueError("Invalid stored expiry") from None
    if expiry.tzinfo is None:
        raise ValueError("Stored expiry must have timezone")
    return {"source": "dhan_web", "expires_at": expiry.astimezone(timezone.utc).isoformat()}
