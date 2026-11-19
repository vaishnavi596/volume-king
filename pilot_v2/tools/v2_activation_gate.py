"""Production V2 activation gate: prove local private provisioning before systemd.

Operator supplies a V2-only environment file containing *paths*, not keys.
No V1 writes, login enrollment, service start, HTTP requests, Dhan calls or orders.
Keep sensitive contents out of stdout/stderr and CI logs.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat

from pilot_v2.oracle_secure_entrypoint import from_private_config

ENV_KEYS = ("BOTKING_V2_MASTER_DEVICE_ID", "BOTKING_V2_MASTER_PUBLIC_DER_PATH",
            "BOTKING_V2_PAIRING_KEY_PATH", "BOTKING_V2_DB_PATH")
SAFE_PREFIX = "/home/opc/botking-v2-private/"


def verify_configuration(environ):
    """Must be fully provisioned and independently approved; never bootstrap."""
    if any(type(environ.get(k)) is not str or not environ[k] for k in ENV_KEYS):
        raise ValueError("V2 Master/key configuration incomplete")
    filenames = [environ[k] for k in ENV_KEYS[1:]]
    if len(set(filenames)) != len(filenames) or any(
        not name.startswith(SAFE_PREFIX) or
        ".." in Path(name).parts or not Path(name).is_absolute()
        for name in filenames
    ):
        raise ValueError("Only dedicated absolute V2 private paths allowed")
    # Entrypoint loads the genuine Master record, verifies SPKI and private
    # pairing file; a synthetic or missing record can never pass this gate.
    app = from_private_config(
        device_id=environ[ENV_KEYS[0]],
        master_der_path=environ[ENV_KEYS[1]],
        pairing_path=environ[ENV_KEYS[2]],
        db_path=environ[ENV_KEYS[3]],
    )
    from fastapi.testclient import TestClient
    client = TestClient(app)
    if client.get("/v2-pilot/quotes").status_code != 401:
        raise ValueError("V2 unauthenticated read gate failed")
    if client.get("/v2-pilot/orders").status_code != 404:
        raise ValueError("Orders route must not exist")
    if client.post("/v2-pilot/auth/challenge",
                   json={"device_id": "unknown-unapproved-device"}).status_code != 403:
        raise ValueError("Unapproved device challenge must be denied")
    return True


def parse_private_environment(path):
    """Read owner-protected environment paths only; reject shell evaluation."""
    p = Path(path)
    if (not p.is_absolute() or p.is_symlink() or not p.is_file() or
        stat.S_IMODE(p.stat().st_mode) & 0o077 or p.stat().st_size > 2048 or
        p.parent.is_symlink() or
        stat.S_IMODE(p.parent.stat().st_mode) & 0o077):
        raise ValueError("V2 environment file must be private")
    env = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or key not in ENV_KEYS or key in env or not value:
            raise ValueError("Invalid V2 environment key")
        if any(c in value for c in ("'", '"', "$", "`", "\\", " ", "\t", "\r")):
            raise ValueError("Unsafe V2 environment value")
        env[key] = value
    if set(env) != set(ENV_KEYS):
        raise ValueError("Missing V2 operator configuration")
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-env-file", required=True)
    a = parser.parse_args()
    try:
        verify_configuration(parse_private_environment(a.private_env_file))
    except Exception:
        print("V2_ACTIVATION_GATE=BLOCKED; NO_CREDENTIALS_PRINTED; NO_CHANGES")
        raise SystemExit(1)
    print("V2_ACTIVATION_GATE=APPROVED_LOCAL_AUTH_ONLY; LIVE_DATA=NOT_VERIFIED")


if __name__ == "__main__":
    main()
