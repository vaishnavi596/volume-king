"""Read-only gate before enabling Dhan consent token persistence on Oracle.

Run as the actual bot-king.service user. No token contents, network calls,
service changes, or writes. Exit 0 means filesystem prerequisites only.
"""
import os
from pathlib import Path
import stat
import sys


def check_storage_readiness(path, uid=None):
    uid = os.geteuid() if uid is None else uid
    target = Path(path)
    parent = target.parent
    issues = []
    if parent.is_symlink() or not parent.is_dir():
        issues.append("credential_directory_invalid")
        return issues
    info = parent.stat()
    if info.st_mode & 0o022:
        issues.append("credential_directory_writable_by_others")
    if info.st_uid != uid or not os.access(parent, os.W_OK | os.X_OK):
        issues.append("service_user_cannot_atomically_replace_token")
    if target.is_symlink():
        issues.append("token_path_symlink")
    elif target.exists():
        file_info = target.stat()
        if not stat.S_ISREG(file_info.st_mode):
            issues.append("token_path_not_regular")
        if file_info.st_uid != uid:
            issues.append("token_file_owned_by_other_user")
        if stat.S_IMODE(file_info.st_mode) & 0o077:
            issues.append("token_file_permissions_not_0600")
    return issues


def main():
    path = os.environ.get("DHAN_TOKEN_FILE", "/etc/bot-king/dhan-token")
    problems = check_storage_readiness(path)
    if problems:
        for issue in problems:
            print("DHAN_PERSISTENCE_GATE=" + issue)
        return 2
    print("DHAN_PERSISTENCE_GATE=filesystem_ready")
    print("DHAN_AUTO_RENEWAL=not_enabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
