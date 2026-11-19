"""Standalone V2-only HTTP route shell: DISABLED until trusted integrations exist.

No V1 imports, broker calls, provider fallbacks, key enrollment, or order routes.
This module intentionally cannot claim authenticated/live data.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

MAX_AUTH_BODY = 1024


def create_app():
    app = FastAPI(title="BOT KING V2 Isolated Gateway",
                  docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/v2-pilot/health")
    def health():
        return {"service": "botking-v2-pilot", "status": "staged_disabled",
                "live_data": False, "live_orders_enabled": False}

    async def auth_unavailable(request: Request):
        # Fixed bounded body guard: never parse, echo or log a submitted secret.
        if request.headers.get("content-length"):
            try:
                n = int(request.headers["content-length"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid content length")
            if n < 0 or n > MAX_AUTH_BODY:
                raise HTTPException(status_code=413, detail="Request too large")
        raise HTTPException(status_code=503, detail="V2 trusted device enrollment unavailable")

    @app.post("/v2-pilot/auth/challenge")
    async def challenge(request: Request):
        return await auth_unavailable(request)

    @app.post("/v2-pilot/auth/login")
    async def login(request: Request):
        return await auth_unavailable(request)

    def feed_unavailable(request: Request):
        bearer = request.headers.get("authorization", "")
        if not bearer.startswith("Bearer ") or len(bearer) < 32:
            raise HTTPException(status_code=401, detail="Verified device login required")
        raise HTTPException(status_code=503, detail="V2 trusted data pipeline unavailable")

    @app.get("/v2-pilot/indices")
    def indices(request: Request):
        return feed_unavailable(request)

    @app.get("/v2-pilot/quotes")
    def quotes(request: Request):
        return feed_unavailable(request)

    @app.exception_handler(HTTPException)
    async def sanitized_error(request, exc):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code,
                            headers={"Cache-Control": "no-store"})

    return app
