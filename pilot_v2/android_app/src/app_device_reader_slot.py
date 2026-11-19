"""Single app-owned, in-memory trusted P-256 sign-in reader slot.

No user-entered bearer, fake role, persisted token or auto-login. Actual P-256
signature still requires a separately reviewed Android Keystore callback.
The server independently checks device proof and scope on each read.
"""
from app_p256_login import V2P256LoginHTTPSClient
from secure_https_reader import FeedError, V2ReadonlyHTTPSReader


class DeviceReaderSlot:
    def __init__(self):
        self._reader = None

    @property
    def reader(self):
        """May be inactive after server rejection; use status for diagnostics."""
        return self._reader

    def clear(self):
        """Local scrub ONLY. Does not revoke a bearer on the remote server."""
        if self._reader is not None:
            self._reader.invalidate()
            self._reader = None

    def sign_in(self, login_client):
        """Accept only a successful signed HTTPS login, never a token string."""
        if type(login_client) is not V2P256LoginHTTPSClient:
            raise FeedError("Approved P-256 HTTPS login client required")
        self.clear()  # Rotate session; failed sign-in must leave no old bearer.
        reader = login_client.login()
        if type(reader) is not V2ReadonlyHTTPSReader:
            raise FeedError("Approved read-only device session required")
        self._reader = reader
        return True

    def active_reader(self):
        reader = self._reader
        if reader is None or not reader.session_active:
            raise FeedError("V2 device session sign-in required")
        return reader
