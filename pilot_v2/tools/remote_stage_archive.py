"""Fail-closed V2-only staging of a GitHub Actions source archive.

Runs on Oracle under opc, not as root. No service activation or V1 writes.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import stat
import tarfile

MAX_ARCHIVE = 8_000_000
MAX_FILES = 120
MAX_FILE = 1_000_000
REQUIRED_TOOLS = {"tools/v2_activation_gate.py", "tools/provision_oracle_master.py"}
REQUIRED = {
    "unified_gateway_app.py", "unified_data_pipeline.py",
    "internal_dhan_read_port.py", "trusted_http_adapter.py",
    "oracle_dhan_read_transport.py", "isolated_gateway_app.py",
}


def stage(archive, *, sha, checksum, root):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Exact Git commit SHA required")
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("Exact source archive SHA-256 required")
    archive = Path(archive)
    requested_root = Path(root)
    if requested_root.is_symlink():
        raise ValueError("Staging root must not be a symlink")
    root = requested_root.resolve()
    if root != Path.home().resolve() / "botking-v2-staging":
        raise ValueError("Unexpected staging root")
    target = root / ("gh-" + sha)
    if target.exists() or target.is_symlink():
        raise FileExistsError("Refuse to overwrite staged commit")
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Unsafe source archive")
    raw = archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError("Source archive hash mismatch")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
        for member in tf:
            if (not member.isfile() or member.size > MAX_FILE
                    or not (re.fullmatch(r"[a-zA-Z0-9_]+\.py", member.name)
                            or re.fullmatch(r"tools/[a-zA-Z0-9_]+\.py", member.name))
                    or member.name in files or len(files) >= MAX_FILES):
                raise ValueError("Unsafe or duplicate source archive member")
            content = tf.extractfile(member).read(MAX_FILE + 1)
            if len(content) != member.size:
                raise ValueError("Incomplete archive member")
            compile(content, member.name, "exec")
            files[member.name] = content
    if not REQUIRED.issubset(files) or not REQUIRED_TOOLS.issubset(files):
        raise ValueError("Incomplete V2 gateway source")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if stat.S_IMODE(root.stat().st_mode) & 0o077:
        raise ValueError("Staging root must be private")
    # Never publish a partially written commit: retrying the exact SHA must
    # remain possible after a disk/write failure without overwriting a release.
    pending = root / (".pending-gh-" + sha)
    if pending.exists() or pending.is_symlink():
        raise FileExistsError("Existing incomplete staging transaction")
    pending.mkdir(mode=0o700)
    try:
        source = pending / "pilot_v2"
        source.mkdir(mode=0o700)
        for name, content in sorted(files.items()):
            path = source / name
            if name.startswith("tools/"):
                (source / "tools").mkdir(mode=0o700, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o600)
        manifest = {"commit": sha, "archive_sha256": checksum,
                    "source_count": len(files), "activated": False}
        manifest_file = pending / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, sort_keys=True) + "\n")
        manifest_file.chmod(0o600)
        pending.rename(target)
    except BaseException:
        shutil.rmtree(pending)
        raise
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--checksum", required=True)
    p.add_argument("--root", required=True)
    a = p.parse_args()
    print(json.dumps(stage(a.archive, sha=a.sha, checksum=a.checksum,
                           root=a.root), sort_keys=True))


if __name__ == "__main__":
    main()
