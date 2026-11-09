"""Secure, opt-in Dhan token persistence primitives; no network or renewal.

NOT wired into production. Call only after Dhan authentication succeeds and
expiry/account have been validated by the gateway. Never log token contents.
"""
import os
from pathlib import Path
import tempfile


def atomic_store_token(path, token):
    """Replace a token file atomically with owner-only permissions (0600).

    Requires an existing private parent directory; does not change ownership.
    The caller must ensure the service user can read the resulting file.
    """
    target = Path(path)
    if not isinstance(token, str) or not token or token != token.strip() or "\n" in token or "\r" in token:
        raise ValueError("Invalid token")
    parent = target.parent
    if not parent.is_dir():
        raise FileNotFoundError("Token directory missing")
    if parent.is_symlink() or target.is_symlink():
        raise ValueError("Symlink paths not permitted")
    if os.stat(parent).st_mode & 0o022:
        raise PermissionError("Token directory must not be group/world writable")
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".dhan-token-", dir=str(parent))
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(token + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
        tmp = None
        dirfd = os.open(str(parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if tmp is not None:
            os.unlink(tmp)
