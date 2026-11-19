"""One-command isolated ASGI HTTP gate for previously staged V2 gateway.

Creates ONLY ~/botking-v2-staging/runtime-venv. No server start, secrets,
Dhan request, V1 modification, broker order or pretend-live success.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

# Versions are isolated to this venv; CI/runtime evidence must be recorded.
DEPS = ("fastapi==0.115.12", "httpx==0.28.1")


def inside(base, child):
    base = base.resolve()
    child = child.resolve()
    return child == base or base in child.parents


def verify_source(stage):
    manifest = json.loads((stage / "manifest.json").read_text("utf-8"))
    if (manifest.get("production_ready") is not False or
            manifest.get("oracle_deployed") is not False or
            manifest.get("enabled") is not False or
            manifest.get("source_only") is not True):
        raise ValueError("Fail-closed stage manifest required")
    files = manifest.get("files")
    if not isinstance(files, dict) or "isolated_gateway_app.py" not in files:
        raise ValueError("New gateway module missing in stage")
    for name, expected in files.items():
        if (not isinstance(name, str) or "/" in name or "\\" in name or
                name in (".", "..") or not name.endswith(".py")):
            raise ValueError("Bad staged module path")
        source = stage / "pilot_v2" / name
        if source.is_symlink() or not source.is_file():
            raise ValueError("Missing or symlinked stage module")
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError("Staged module digest changed")
    return manifest


def run_gate(stage, base, install=True):
    if not inside(base, stage) or not inside(base, base / "runtime-venv"):
        raise ValueError("Only V2 isolated workspace allowed")
    manifest = verify_source(stage)
    env_dir = base / "runtime-venv"
    python = env_dir / "bin" / "python"
    if not python.is_file():
        venv.EnvBuilder(with_pip=True, clear=False, system_site_packages=False).create(env_dir)
    if install:
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                        "--no-input", *DEPS], check=True, timeout=180,
                       stdout=subprocess.DEVNULL)
    script = r'''
import importlib.util, json, sys
from fastapi.testclient import TestClient
module_file = sys.argv[1]
spec = importlib.util.spec_from_file_location("staged_v2_isolated_gateway", module_file)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
client = TestClient(module.create_app())
checks = []
def check(label, path, expected, method="get", **kwargs):
    r = getattr(client, method)(path, **kwargs)
    checks.append({"name": label, "expected": expected, "actual": r.status_code,
                   "pass": r.status_code == expected})
    if r.status_code != expected:
        raise RuntimeError("ASGI response contract mismatch: " + label)
    return r
health = check("v2_disabled_health", "/v2-pilot/health", 200)
assert health.json()["live_data"] is False and health.json()["live_orders_enabled"] is False
for name in ("challenge", "login"):
    check("disabled_" + name, "/v2-pilot/auth/" + name, 503,
          method="post", json={"device_id": "not-enrolled"})
for name in ("quotes", "indices"):
    check("unauthorized_" + name, "/v2-pilot/" + name, 401)
    check("no_untrusted_bearer_" + name, "/v2-pilot/" + name, 503,
          headers={"Authorization": "Bearer " + "X" * 48})
check("no_v1_health", "/health", 404)
check("no_order_api", "/v2-pilot/orders", 404)
print(json.dumps({"status": "ISOLATED_ASGI_TEST_PASS", "checks": checks,
                  "live_data": False, "activated": False}))
'''
    result = subprocess.run([str(python), "-c", script,
                             str(stage / "pilot_v2" / "isolated_gateway_app.py")],
                            text=True, capture_output=True, timeout=30, check=True)
    return {"source_commit": manifest["commit"], **json.loads(result.stdout)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, type=Path)
    args = parser.parse_args()
    base = Path.home() / "botking-v2-staging"
    try:
        result = run_gate(args.stage, base)
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "ISOLATED_ASGI_BLOCKED",
                          "reason": type(exc).__name__, "activated": False}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
