"""Provider-neutral, credential-free market data routing decisions.

This is preparation for Dhan/Oracle integration, not an authenticated connector.
Never silently relabel Yahoo data as Dhan or Angel One data.
"""
from dataclasses import dataclass
from typing import Literal

Provider = Literal["Yahoo Finance", "Dhan", "Angel One"]
Status = Literal["NOT_CONFIGURED", "CONNECTED", "EXPIRED", "UNAVAILABLE", "RATE_LIMITED"]

PROVIDERS = ("Yahoo Finance", "Dhan", "Angel One")
BROKER_PROVIDERS = ("Dhan", "Angel One")


@dataclass(frozen=True)
class ProviderState:
    provider: Provider
    status: Status
    quote_timestamp: float | None = None
    checked_at: float | None = None

    def __post_init__(self):
        if self.provider not in PROVIDERS:
            raise ValueError("Unknown market data provider")
        if self.status not in ("NOT_CONFIGURED", "CONNECTED", "EXPIRED", "UNAVAILABLE", "RATE_LIMITED"):
            raise ValueError("Unknown provider status")


def choose_source(states, preferred="Dhan", now=None, max_age_seconds=180):
    """Select a fresh, verified source or return an explicit unavailable result.

    Caller must supply provider-verified states and timestamps; this function
    does not authenticate, refresh tokens, or combine mismatched contracts.
    """
    if preferred not in PROVIDERS:
        raise ValueError("Unknown preferred provider")
    if max_age_seconds < 0:
        raise ValueError("Maximum quote age must be nonnegative")
    if now is None:
        import time
        now = time.time()
    by_name = {s.provider: s for s in states}
    order = (preferred,) + tuple(p for p in PROVIDERS if p != preferred)
    for provider in order:
        state = by_name.get(provider)
        if not state or state.status != "CONNECTED" or state.quote_timestamp is None:
            continue
        age = now - state.quote_timestamp
        if 0 <= age <= max_age_seconds:
            return {"status": "AVAILABLE", "provider": provider, "age_seconds": age,
                    "fallback": provider != preferred}
    return {"status": "UNAVAILABLE", "provider": None, "age_seconds": None,
            "fallback": False}
