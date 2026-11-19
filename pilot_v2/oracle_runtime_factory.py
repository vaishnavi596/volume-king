"""Explicit Oracle V2 runtime composition, never self-enrolling a phone.

Only the server operator may supply the local private broker pairing key and an
independently approved P-256 MASTER public key. No order endpoint is installed.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import RLock
import os
import stat
import time

from .atomic_verified_login import AtomicVerifiedLogin
from .durable_challenges import DurableP256ChallengeVerifier
from .durable_device_sessions import DurableDeviceSessions
from .durable_device_keys import DurableDeviceKeys
from .internal_dhan_read_port import InternalDhanReadPort
from .oracle_dhan_read_transport import OracleDhanReadTransport
from .shared_read_budget import SharedReadBudget
from .oracle_evidence_lane import OracleDhanEvidenceLane
from .unified_data_pipeline import V2UnifiedReadPipeline, PipelineUnavailable
from .unified_gateway_app import create_v2_unified_app


def create_oracle_v2_runtime(*, db_path, master_device_id, master_public_der,
                             pairing_key, selected_equities=(),
                             transport=None, clock=None, monotonic=None,
                             roster_persistor=None, evidence_transport=None):
    """Build only from operator-supplied, independently enrolled secrets.

    A missing/unapproved master never triggers bootstrap. The SQLite parent
    and DB file must be private, not world-readable or symlinked.
    """
    if type(master_device_id) is not str or not master_device_id:
        raise ValueError("Trusted master identity required")
    if type(master_public_der) is not bytes or not master_public_der:
        raise ValueError("Trusted public P-256 enrollment required")
    if type(pairing_key) is not str or len(pairing_key) < 32:
        raise ValueError("Private Oracle pairing key required")
    path = Path(db_path)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("Pre-enrolled private durable DB required")
    parent = path.parent
    if (parent.is_symlink() or
            stat.S_IMODE(parent.stat().st_mode) & 0o077 or
            stat.S_IMODE(path.stat().st_mode) & 0o077):
        raise ValueError("Durable auth DB and parent must be private")
    if not os.access(path, os.R_OK | os.W_OK):
        raise ValueError("Durable auth DB not writable")
    sessions = DurableDeviceSessions(path)
    with sessions._db() as db:
        approved = db.execute(
            "SELECT master,enabled FROM devices WHERE device=?",
            (master_device_id,)).fetchone()
    if approved != (1, 1):
        raise ValueError("Master must be independently enrolled and enabled")
    keys = DurableDeviceKeys(sessions)
    verifier = DurableP256ChallengeVerifier(path, {master_device_id: master_public_der},
                                              trusted_key_resolver=keys.public_key)
    login = AtomicVerifiedLogin(verifier, sessions)
    mono = monotonic or time.monotonic
    provider = transport if transport is not None else OracleDhanReadTransport(
        pairing_key=pairing_key)
    if transport is not None and not callable(transport):
        raise ValueError("Approved test transport required")
    if roster_persistor is not None and not callable(roster_persistor):
        raise ValueError("Protected roster persistor required")
    if evidence_transport is not None and not callable(evidence_transport):
        raise ValueError("Approved private evidence collector required")
    port = InternalDhanReadPort(transport=provider, selected_equities=selected_equities)
    budget = SharedReadBudget(monotonic=mono)
    pipe = V2UnifiedReadPipeline(
        read_port=port,
        clock=clock or (lambda: datetime.now().astimezone()),
        monotonic=mono,
        read_budget=budget,
    )
    change_lock = RLock()
    def trusted_master_roster_update(symbols):
        if roster_persistor is None:
            raise PipelineUnavailable("Private roster persistor unavailable")
        try:
            selected = InternalDhanReadPort._validated_equities(symbols)
        except (ValueError, TypeError):
            raise ValueError("Invalid selected equity roster") from None
        with change_lock:
            try:
                roster_persistor(selected)
            except (OSError, ValueError, TypeError):
                raise PipelineUnavailable("Private roster persistence unavailable") from None
            pipe.replace_selected_equities(selected)
        return len(selected)

    return create_v2_unified_app(
        verified_login=login, data_pipeline=pipe,
        master_roster_updater=(trusted_master_roster_update
                              if roster_persistor is not None else None),
        evidence_provider=(OracleDhanEvidenceLane(
            transport=evidence_transport, read_budget=budget,
            monotonic=mono, clock=time.time)
            if evidence_transport is not None else None))
