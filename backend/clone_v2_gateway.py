"""Separate B2 clone-only Oracle login gateway, SSK authenticated and read-only.

Never reuse/deploy the old V2 pilot or modify the running V1 service.
Owner operates this on 127.0.0.1:8002 behind a reviewed HTTPS proxy. No
market quote/candle endpoints or broker trading orders are added here.
"""
from __future__ import annotations

import hmac
import os
import stat
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

KEY_ENV = "BOTKING_CLONE_V2_SSK_FILE"
PROTOCOL = "botking-clone-v2"


def private_ssk(path):
    """Load an operator-protected key without exposing bytes in logs."""
    if (type(path) is not str or not path.startswith("/home/opc/")
            or not Path(path).is_absolute() or ".." in Path(path).parts):
        raise ValueError("Clone V2 private SSK path required")
    p = Path(path)
    if (p.is_symlink() or not p.is_file() or p.parent.is_symlink()
            or stat.S_IMODE(p.parent.stat().st_mode) & 0o077
            or stat.S_IMODE(p.stat().st_mode) & 0o077
            or p.stat().st_size < 32 or p.stat().st_size > 1024):
        raise ValueError("Clone V2 private SSK missing or unprotected")
    key = p.read_bytes().strip()
    if len(key) < 32 or len(key) > 512 or any(c < 33 or c > 126 for c in key):
        raise ValueError("Clone V2 SSK format invalid")
    return key


def create_app(*, key_bytes=None):
    """Fail closed at startup if owner has not provisioned a protected key."""
    if key_bytes is None:
        key_bytes = private_ssk(os.environ.get(KEY_ENV))
    if (type(key_bytes) is not bytes or not 32 <= len(key_bytes) <= 512
            or any(c < 33 or c > 126 for c in key_bytes)):
        raise ValueError("Approved Clone V2 SSK required")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/clone-v2/status")
    def status(x_botking_key: str | None = Header(default=None)):
        # Constant-time authorization, including unknown or malformed keys.
        if (not isinstance(x_botking_key, str)
                or len(x_botking_key) > 1024
                or not hmac.compare_digest(
                    x_botking_key.encode("utf-8"), key_bytes)):
            raise HTTPException(403, "Clone V2 server access denied")
        return JSONResponse(
            {"protocol": PROTOCOL, "authenticated": True, "read_only": True,
             "live_orders_enabled": False, "pipeline": "dhan-oracle-clone",
             "status": "ready"},
            headers={"Cache-Control": "no-store"})

    @app.get("/clone-v2/health")
    def health():
        # Health is not proof of authorization or live market data.
        return JSONResponse(
            {"status": "gateway_process_ready", "live_data_verified": False,
             "live_orders_enabled": False},
            headers={"Cache-Control": "no-store"})

    return app
