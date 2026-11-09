"""Opt-in bridge from verified Dhan consent response to private token storage.

Not connected to BOT KING's production callback. No renewal or network calls.
"""
from pathlib import Path

try:
    from .dhan_consent_validation import validate_consent_response
    from .dhan_token_storage import atomic_store_token, read_persisted_token
except ImportError:
    from dhan_consent_validation import validate_consent_response
    from dhan_token_storage import atomic_store_token, read_persisted_token


def persist_verified_consent(payload, expected_client_id, token_path, now=None):
    """Validate before writing. Return only the verified UTC expiry, never token."""
    token, expiry = validate_consent_response(payload, expected_client_id, now=now)
    atomic_store_token(Path(token_path), token)
    return expiry


def load_verified_token(token_path):
    """Read only a previously secured token; validity still requires Dhan check."""
    return read_persisted_token(Path(token_path))
