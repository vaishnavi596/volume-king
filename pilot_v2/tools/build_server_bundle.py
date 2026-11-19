"""Create an isolated, reproducible V2 server *source* staging archive.

Never copies Oracle V1 files, calls Dhan, deploys, or enables an HTTP route.
A built bundle is NOT a deployable authenticated live gateway.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import zipfile

SOURCE_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("http_gateway.py", "api_contract.py", "device_sessions.py",
            "durable_device_sessions.py", "verified_login_gateway.py",
            "durable_challenges.py", "atomic_verified_login.py",
                "unified_gateway_app.py", "unified_data_pipeline.py", "internal_dhan_read_port.py", "shared_read_budget.py", "trusted_http_adapter.py", "private_backup_vault.py", "isolated_gateway_app.py",
                "oracle_secure_entrypoint.py", "oracle_runtime_factory.py",
                "oracle_dhan_read_transport.py")


REQUIRED_TOOLS = ("tools/v2_activation_gate.py", "tools/provision_oracle_master.py")


def build(output: Path, source_root: Path = SOURCE_ROOT) -> dict:
    source_root = source_root.resolve(strict=True)
    if source_root.name != "pilot_v2":
        raise ValueError("Only pilot_v2 source may be bundled")
    for name in REQUIRED:
        if not (source_root / name).is_file():
            raise FileNotFoundError("Missing V2 source: " + name)
    for name in REQUIRED_TOOLS:
        if not (source_root / name).is_file():
            raise FileNotFoundError("Missing V2 protected tool: " + name)
    files = sorted(source_root.glob("*.py"))
    files += sorted(source_root / name for name in REQUIRED_TOOLS)
    files += sorted((source_root / "tools").glob("verify_v2_gateway_routes.py"))
    if not files:
        raise ValueError("Empty V2 source bundle")
    manifest = {"kind": "bot-king-v2-isolated-source-only",
                "production_ready": False,
                "enabled": False,
                "oracle_deployed": False,
                "files": {}}
    entries = []
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Symlinks/nonfiles forbidden")
        if stat.S_IMODE(path.stat().st_mode) & 0o002:
            raise ValueError("World writable source forbidden")
        data = path.read_bytes()
        if len(data) > 1_000_000:
            raise ValueError("Oversize source")
        relative = path.relative_to(source_root).as_posix()
        if not relative.endswith(".py") or relative.startswith("android_app/"):
            raise ValueError("Invalid V2 source path")
        manifest["files"][relative] = hashlib.sha256(data).hexdigest()
        entries.append(("pilot_v2/" + relative, data))
    output = output.resolve()
    if output.exists():
        raise FileExistsError("Refuse to overwrite bundle")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        info = zipfile.ZipInfo("manifest.json", (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, manifest_bytes)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = build(args.output)
    print(json.dumps({"output": str(args.output), "source_count": len(manifest["files"]),
                      "production_ready": False, "oracle_deployed": False}))


if __name__ == "__main__":
    main()
