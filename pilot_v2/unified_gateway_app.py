"""The one V2 application composition root: auth -> unified read pipeline.

This factory cannot create a provider, enroll a device, or enable live Dhan
by itself. Dhan transport and trusted device keys must be provisioned securely
out of band. Unsupported source lanes remain unavailable, not fake-live.
"""
from __future__ import annotations

from .atomic_verified_login import AtomicVerifiedLogin
from .trusted_http_adapter import create_trusted_app
from .unified_data_pipeline import V2UnifiedReadPipeline
from .private_backup_vault import ServerBackupVault, create_private_backup_router
from .durable_device_sessions import DurableDeviceSessions


def create_v2_unified_app(*, verified_login, data_pipeline, private_backup_vault=None):
    if not isinstance(verified_login, AtomicVerifiedLogin):
        raise ValueError("Verified durable P256 login required")
    if not isinstance(data_pipeline, V2UnifiedReadPipeline):
        raise ValueError("One trusted V2 data pipeline required")
    # Authentication is checked for every HTTP feed request by trusted adapter.
    # Do not instantiate independent device-facing per-feature gateways.
    if private_backup_vault is not None:
        if not isinstance(private_backup_vault, ServerBackupVault):
            raise ValueError("Explicit verified private backup vault required")
        resolver = private_backup_vault._master_owner
        if (getattr(resolver, "__self__", None) is not verified_login._sessions
                or getattr(resolver, "__func__", None)
                is not DurableDeviceSessions.authorize_master):
            raise ValueError("Vault must use the same revocable Master sessions")
    app = create_trusted_app(
        login=verified_login,
        snapshot_provider=lambda device, feed: data_pipeline.dispatch(device, feed),
    )
    if private_backup_vault is not None:
        # Disabled by default; mount only a vault bound to THIS signed login.
        app.include_router(create_private_backup_router(private_backup_vault))
    return app
