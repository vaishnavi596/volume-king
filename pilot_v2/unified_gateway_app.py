"""The one V2 application composition root: auth -> unified read pipeline.

This factory cannot create a provider, enroll a device, or enable live Dhan
by itself. Dhan transport and trusted device keys must be provisioned securely
out of band. Unsupported source lanes remain unavailable, not fake-live.
"""
from __future__ import annotations

from .atomic_verified_login import AtomicVerifiedLogin
from .trusted_http_adapter import create_trusted_app
from .unified_data_pipeline import V2UnifiedReadPipeline


def create_v2_unified_app(*, verified_login, data_pipeline):
    if not isinstance(verified_login, AtomicVerifiedLogin):
        raise ValueError("Verified durable P256 login required")
    if not isinstance(data_pipeline, V2UnifiedReadPipeline):
        raise ValueError("One trusted V2 data pipeline required")
    # Authentication is checked for every HTTP feed request by trusted adapter.
    # Do not instantiate independent device-facing per-feature gateways.
    return create_trusted_app(
        login=verified_login,
        snapshot_provider=lambda device, feed: data_pipeline.dispatch(device, feed),
    )
