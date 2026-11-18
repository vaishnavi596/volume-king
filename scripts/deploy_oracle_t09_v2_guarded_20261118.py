#!/usr/bin/env python3
"""Owner-authorized T09 v2 single-file Oracle install; SHA-locked, reversible.
Run as opc only. No Dhan requests, trading orders, secrets, or live assessment fetch.
Never use with a different candidate or baseline; no server work without preflight.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path("/opt/bot-king-server")
BACKUP = Path("/home/opc/botking-t09-backup-iVpgPT")
CANDIDATE = Path("/tmp/botking-t09-v2-xwx0l7j8/server.py")
ORIGINAL = {
    "server.py": "c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac",
    "assessment_state.py": "ea2db1787be5cddc1ff2235db6592c7858519fc97b18d8c65c011ef9c7a3e3d2",
    "assessment_api.py": "f421292725adadd825cbfa2a2a14f358aa6d07f29e3d71c0aa073d4b2827a2a5",
}
CANDIDATE_SHA = "9327e33a204e06affad383bd8af80ae0ed5f90bc79ee2b1410cadcb7fc5e12b5"
TARGET = ROOT / "server.py"
SERVICE = "bot-king.service"
REPORT = {"audit": "T09_V2_GUARDED_SINGLE_FILE_DEPLOY",
          "baseline_sha": ORIGINAL["server.py"],
          "candidate_sha": CANDIDATE_SHA,
          "backup": str(BACKUP),
          "production_changed": False,
          "server_restarted": False,
          "dhan_requests": 0,
          "orders_sent": 0}
mutated = False

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def verified(path, sha, syntax=True):
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("HOLD_MISSING_OR_SYMLINK_" + path.name)
    raw = path.read_bytes()
    if digest(raw) != sha:
        raise RuntimeError("HOLD_SHA_DRIFT_" + path.name)
    if syntax:
        ast.parse(raw.decode("utf-8"))
    return raw

def run(*cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise RuntimeError("COMMAND_FAILED_" + cmd[-1] + "_RC_" + str(result.returncode))
    return result.stdout.strip()

def sudo(*cmd):
    return run("sudo", "-n", *cmd)

def http_status(path):
    request = Request("http://127.0.0.1:8000" + path,
                      headers={"User-Agent": "BOTKING-T09-guarded/1"})
    try:
        with urlopen(request, timeout=3) as response:
            return response.status
    except HTTPError as exc:
        return exc.code
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("LOCAL_HTTP_UNAVAILABLE") from exc

def health():
    if run("systemctl", "is-active", SERVICE) != "active":
        raise RuntimeError("SERVICE_INACTIVE")
    if http_status("/health") != 200:
        raise RuntimeError("HEALTH_NOT_200")
    if http_status("/v2/assessment/NIFTY") != 403:
        raise RuntimeError("UNAUTH_ASSESSMENT_NOT_403")

def wait_health():
    last = None
    for _ in range(12):
        try:
            health()
            return
        except Exception as exc:
            last = type(exc).__name__
            time.sleep(1)
    raise RuntimeError("POSTFLIGHT_HEALTH_AUTH_FAILED_" + str(last))

def install(src):
    # Fixed target; stage on same filesystem before atomic replacement.
    tmp = ROOT / ".server.py.t09-pending"
    sudo("install", "-o", "root", "-g", "root", "-m", "0644", str(src), str(tmp))
    try:
        sudo("mv", "-f", str(tmp), str(TARGET))
    except BaseException:
        try:
            sudo("rm", "-f", str(tmp))
        except Exception:
            pass
        raise

def rollback():
    verified(BACKUP / "server.py", ORIGINAL["server.py"])
    install(BACKUP / "server.py")
    sudo("systemctl", "restart", SERVICE)
    wait_health()
    verified(TARGET, ORIGINAL["server.py"])
    REPORT["rollback"] = "PASS"
    REPORT["production_changed"] = False

def main():
    global mutated
    if os.geteuid() == 0:
        raise RuntimeError("RUN_AS_OPC_NOT_ROOT")
    for name, sha in ORIGINAL.items():
        verified(ROOT / name, sha)
        verified(BACKUP / name, sha)
    verified(CANDIDATE, CANDIDATE_SHA)
    if run("stat", "-c", "%U:%G:%a", str(TARGET)) != "root:root:644":
        raise RuntimeError("HOLD_UNEXPECTED_TARGET_OWNER_OR_MODE")
    if run("df", "-Pk", str(ROOT)).splitlines()[-1].split()[3].isdigit() is False:
        raise RuntimeError("HOLD_DISK_STAT")
    sudo("true")
    health()
    REPORT["preflight"] = "PASS"
    # Everything above runs before first production write.
    mutated = True
    install(CANDIDATE)
    REPORT["production_changed"] = True
    verified(TARGET, CANDIDATE_SHA)
    sudo("systemctl", "restart", SERVICE)
    REPORT["server_restarted"] = True
    wait_health()
    verified(TARGET, CANDIDATE_SHA)
    REPORT["postflight"] = "HEALTH_200_UNAUTH_403"
    REPORT["status"] = "DEPLOY_HEALTH_AUTH_PASS_RUNTIME_PUBLISH_READ_PENDING"

def execute():
    global mutated
    try:
        main()
    except BaseException as exc:
        REPORT["error_type"] = type(exc).__name__
        REPORT["error_stage"] = "AFTER_FIRST_WRITE" if mutated else "PREFLIGHT"
        if mutated:
            try:
                rollback()
                REPORT["status"] = "ROLLED_BACK_SAFE"
            except BaseException as rollback_exc:
                REPORT["rollback"] = "FAILED_" + type(rollback_exc).__name__
                REPORT["status"] = "EMERGENCY_HOLD_REQUIRES_OPERATOR"
        else:
            REPORT["status"] = "HOLD_NO_PRODUCTION_WRITE"
    print(json.dumps(REPORT, indent=2, sort_keys=True))
    return 0 if REPORT["status"] == "DEPLOY_HEALTH_AUTH_PASS_RUNTIME_PUBLISH_READ_PENDING" else 2

if __name__ == "__main__":
    sys.exit(execute())
