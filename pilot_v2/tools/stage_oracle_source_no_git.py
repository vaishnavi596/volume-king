"""Prepare a V2-only source tree from a pinned GitHub archive.

Stage only. Never start a service, call Dhan, or touch V1.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import urllib.request
import zipfile

REPO = "vaishnavi596/volume-king"
MAX_ARCHIVE = 30_000_000
MAX_FILE = 1_000_000
MAX_FILES = 250
REQUIRED = frozenset((
    "http_gateway.py", "api_contract.py", "device_sessions.py",
    "durable_device_sessions.py", "verified_login_gateway.py",
    "durable_challenges.py", "atomic_verified_login.py",
    "unified_gateway_app.py", "unified_data_pipeline.py",
    "internal_dhan_read_port.py", "shared_read_budget.py",
    "trusted_http_adapter.py", "private_backup_vault.py",
    "isolated_gateway_app.py",
))


def validate_commit(sha: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("A pinned 40-character lowercase commit SHA is required")
    return sha


def unpack(data: bytes, destination: Path, sha: str) -> dict:
    validate_commit(sha)
    if len(data) > MAX_ARCHIVE:
        raise ValueError("Archive too large")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Staging destination exists")
    if destination.resolve().is_relative_to(Path("/opt/bot-king-server")):
        raise ValueError("V1 production location forbidden")
    selected = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for item in z.infolist():
            p = PurePosixPath(item.filename)
            parts = p.parts
            if item.is_dir() or len(parts) < 3:
                continue
            if not parts[0].endswith("-" + sha[:7]) or parts[1] != "pilot_v2":
                continue
            relative = PurePosixPath(*parts[2:])
            if (relative.is_absolute() or ".." in relative.parts or
                not all(s and s not in (".", "..") for s in relative.parts)):
                raise ValueError("Unsafe archive member")
            if len(relative.parts) != 1 or relative.suffix != ".py":
                continue
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symlink forbidden")
            if item.file_size > MAX_FILE or item.file_size < 0:
                raise ValueError("File too large")
            if relative.name in selected or len(selected) >= MAX_FILES:
                raise ValueError("Duplicate/excess member")
            raw = z.read(item)
            if len(raw) > MAX_FILE:
                raise ValueError("Decompression too large")
            selected[relative.name] = raw

    if not REQUIRED.issubset(selected):
        raise ValueError("Missing required V2 server prototype modules")
    destination.mkdir(mode=0o700, parents=True)
    try:
        (destination / "pilot_v2").mkdir(mode=0o700)
        manifest = {"commit": sha, "source_only": True, "enabled": False,
                    "production_ready": False, "oracle_deployed": False,
                    "files": {}}
        for name, raw in sorted(selected.items()):
            target = destination / "pilot_v2" / name
            target.write_bytes(raw)
            target.chmod(0o600)
            manifest["files"][name] = hashlib.sha256(raw).hexdigest()
        (destination / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (destination / "manifest.json").chmod(0o600)
        return manifest
    except BaseException:
        # Leave failed stage in place for operator inspection; no activation.
        raise



def verify_staged_source(destination: Path, sha: str) -> dict:
    """Read-only integrity audit of a pinned, disabled V2 source stage.

    Detects missing/tampered staged files, unsafe extra files, and false
    'enabled' manifest state. Does not authenticate the manifest's creator;
    its trusted origin must still be the pinned GitHub commit.
    """
    validate_commit(sha)
    destination = Path(destination)
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("Invalid V2 staging directory")
    manifest_path = destination / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("Missing V2 staging manifest")
    if manifest_path.stat().st_size > 50000:
        raise ValueError("Oversize staging manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        raise ValueError("Unreadable staging manifest") from None
    if (type(manifest) is not dict
            or manifest.get("commit") != sha
            or manifest.get("source_only") is not True
            or manifest.get("enabled") is not False
            or manifest.get("production_ready") is not False
            or manifest.get("oracle_deployed") is not False
            or type(manifest.get("files")) is not dict):
        raise ValueError("Unsafe V2 staging manifest")
    listed = manifest["files"]
    source_dir = destination / "pilot_v2"
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise ValueError("Missing V2 stage source directory")
    names = set()
    for p in source_dir.iterdir():
        if p.is_symlink() or not p.is_file() or p.suffix != ".py":
            raise ValueError("Unexpected V2 stage entry")
        names.add(p.name)
    if (names != set(listed) or len(names) > MAX_FILES
            or not REQUIRED.issubset(names)):
        raise ValueError("V2 source manifest/file mismatch")
    for name, expected in listed.items():
        if (type(name) is not str or not re.fullmatch(r"[A-Za-z0-9_]+\.py", name)
                or type(expected) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", expected)):
            raise ValueError("Invalid V2 stage fingerprint")
        path = source_dir / name
        if path.stat().st_size > MAX_FILE:
            raise ValueError("Oversize V2 stage source")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("V2 stage file fingerprint mismatch")
    return {"commit": sha, "files_checked": len(names),
            "integrity": "MATCHED_LOCAL_MANIFEST",
            "production_ready": False, "activated": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True, type=validate_commit)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    dest = args.destination.resolve()
    allowed = Path.home().resolve() / "botking-v2-staging"
    if dest != allowed and allowed not in dest.parents:
        parser.error("Destination must be under ~/botking-v2-staging")
    if args.destination.exists() or args.destination.is_symlink():
        parser.error("Refusing to overwrite an existing destination")
    url = f"https://api.github.com/repos/{REPO}/zipball/{args.commit}"
    request = urllib.request.Request(url, headers={"User-Agent": "bot-king-v2-source-stager",
                                                  "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError("GitHub source fetch did not succeed")
        data = response.read(MAX_ARCHIVE + 1)
    manifest = unpack(data, args.destination, args.commit)
    print(json.dumps({"stage": str(args.destination), "commit": args.commit,
                      "source_count": len(manifest["files"]),
                      "activated": False, "production_changed": False}))


if __name__ == "__main__":
    main()
