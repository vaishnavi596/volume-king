"""Offline-only provider state gateway, separate from legacy Angel One routes.

No broker tokens, login routes, orders, or live network calls.
Deploy only after full tests and explicit approval.
"""
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
import hmac

from backend.provider_router import ProviderState, choose_source, PROVIDERS


class SourceState(BaseModel):
    provider: str
    status: str
    quote_timestamp: float | None = None
    checked_at: float | None = None


class SourceRequest(BaseModel):
    preferred: str = "Dhan"
    allow_fallback: bool = False
    now: float = Field(gt=0)
    max_age_seconds: float = Field(default=180, ge=0, le=86400)
    states: list[SourceState] = Field(max_length=3)


def create_provider_app(pairing_key: str):
    if len(pairing_key) < 32:
        raise ValueError("Gateway pairing key must be at least 32 characters")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    def require_owner(x_botking_key: str | None = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key, pairing_key):
            raise HTTPException(403, "Server access denied")

    @app.post("/v2/providers/select")
    def select(body: SourceRequest, _owner=Depends(require_owner)):
        try:
            states = [ProviderState(x.provider, x.status, x.quote_timestamp, x.checked_at) for x in body.states]
            if len({x.provider for x in states}) != len(states):
                raise ValueError("Duplicate provider")
            return choose_source(states, body.preferred, body.now, body.max_age_seconds, allow_fallback=body.allow_fallback)
        except (ValueError, TypeError):
            raise HTTPException(422, "Invalid provider status") from None

    @app.get("/v2/providers/capabilities")
    def capabilities(_owner=Depends(require_owner)):
        return {"providers": list(PROVIDERS), "dhan_login_enabled": False,
                "live_orders_enabled": False, "mode": "offline-preparation"}

    return app
