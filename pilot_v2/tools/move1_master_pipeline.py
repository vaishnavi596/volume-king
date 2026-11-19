"""One-command, no-git V2 Move-1 staging and fail-closed audit.

NO service deployment, runtime activation, broker orders, or production file edits.
The only write location is ~/botking-v2-staging.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import py_compile
import re
import urllib.error
import urllib.request

from stage_oracle_source_no_git import unpack, MAX_ARCHIVE, validate_commit, REPO

REQUIRED_ROUTES = {
    ("GET", "/v2-pilot/health"),
    ("POST", "/v2-pilot/auth/challenge"),
    ("POST", "/v2-pilot/auth/login"),
    ("GET", "/v2-pilot/indices"),
    ("GET", "/v2-pilot/quotes"),
}
V1_SOURCE = Path("/opt/bot-king-server/server.py")


def route_decorators(source):
    tree = ast.parse(source)
    routes = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr.lower() not in ("get", "post") or not decorator.args:
                continue
            if isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                routes.add((decorator.func.attr.upper(), decorator.args[0].value))
    return routes


def source_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def localhost_health():
    request = urllib.request.Request("http://127.0.0.1:8000/health",
                                    headers={"User-Agent": "botking-v2-move1-audit"})
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=5) as response:
            return response.status
    except (urllib.error.URLError, OSError):
        return None


def run_move1(commit, home=None, archive=None):
    validate_commit(commit)
    base = (home or Path.home()).resolve() / "botking-v2-staging"
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    stage = base / ("move1-" + commit[:12])
    before_sha = source_digest(V1_SOURCE)
    before_health = localhost_health()
    if archive is None:
        url = f"https://api.github.com/repos/{REPO}/zipball/{commit}"
        req = urllib.request.Request(url, headers={"User-Agent": "botking-v2-move1",
                                                   "Accept": "application/vnd.github+json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=30) as response:
            archive = response.read(MAX_ARCHIVE + 1)
    if len(archive) > MAX_ARCHIVE:
        raise ValueError("Oversize source archive")
    manifest = unpack(archive, stage, commit)
    root = stage / "pilot_v2"
    checked = 0
    for path in sorted(root.glob("*.py")):
        py_compile.compile(str(path), doraise=True, cfile=str(base / ("compile-" + path.stem + ".pyc")))
        checked += 1
        if manifest["files"].get(path.name) != source_digest(path):
            raise ValueError("V2 source digest mismatch")
    gateway = root / "isolated_gateway_app.py"
    if not gateway.is_file():
        raise ValueError("New isolated V2 HTTP shell is missing")
    routes = route_decorators(gateway.read_text(encoding="utf-8"))
    if not REQUIRED_ROUTES.issubset(routes):
        raise ValueError("V2 route shape incomplete")
    # Import the isolated factory when FastAPI exists; no port or service is started.
    asgi_routes = None
    try:
        spec = importlib.util.spec_from_file_location("botking_v2_staged_shell", gateway)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = module.create_app()
        asgi_routes = all(
            any(path == route.path and method in route.methods
                for route in app.routes if hasattr(route, "methods"))
            for method, path in REQUIRED_ROUTES
        )
    except ImportError:
        pass  # Missing dependency means runtime remains NOT VERIFIED.
    if asgi_routes is False:
        raise ValueError("Runtime V2 route registration mismatch")
    after_sha = source_digest(V1_SOURCE)
    after_health = localhost_health()
    result = {
        "status": "STAGING_AND_STATIC_AUDIT_PASS",
        "stage": str(stage),
        "commit": commit,
        "source_count": len(manifest["files"]),
        "compiled": checked,
        "route_shapes_present": len(REQUIRED_ROUTES),
        "v1_sha_unchanged": before_sha == after_sha and before_sha is not None,
        "v1_health_before": before_health,
        "v1_health_after": after_health,
        "v2_asgi_routes_registered": asgi_routes,
        "v2_http_runtime_verified": False,
        "v2_trusted_auth_verified": False,
        "v2_dhan_verified": False,
        "activated": False,
        "production_changed": False,
    }
    (base / ("move1-result-" + commit[:12] + ".json")).write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", required=True, type=validate_commit)
    args = p.parse_args()
    try:
        result = run_move1(args.commit)
        print(json.dumps(result, sort_keys=True))
        if not result["v1_sha_unchanged"] or result["v1_health_after"] != 200:
            raise SystemExit("V1 integrity/health did not pass; no activation attempted")
    except Exception as exc:
        print(json.dumps({"status": "MOVE1_BLOCKED", "reason": type(exc).__name__,
                          "activated": False, "production_changed": False}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
