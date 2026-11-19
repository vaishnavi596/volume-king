"""Single app-owned, in-memory trusted P-256 sign-in reader slot.

No user-entered bearer, fake role, persisted token or auto-login. Actual P-256
signature still requires a separately reviewed Android Keystore callback.
The server independently checks device proof and scope on each read.
"""
from threading import Lock
from app_p256_login import V2P256LoginHTTPSClient
from app_keystore_login_binding import AndroidKeystoreLoginBinding
from secure_https_reader import FeedError, V2ReadonlyHTTPSReader


class DeviceReaderSlot:
    def __init__(self):
        self._reader = None
        self._lock = Lock()
        self._generation = 0

    @property
    def reader(self):
        """May be inactive after server rejection; use status for diagnostics."""
        with self._lock:
            return self._reader

    def clear(self):
        """Local scrub ONLY. Does not revoke a bearer on the remote server."""
        with self._lock:
            self._generation += 1
            reader, self._reader = self._reader, None
        if reader is not None:
            reader.invalidate()

    def _begin_sign_in(self):
        """Reserve a cancellable attempt before any platform/network work."""
        with self._lock:
            self._generation += 1
            attempt = self._generation
            previous, self._reader = self._reader, None
        if previous is not None:
            previous.invalidate()
        return attempt

    def _complete_sign_in(self, login_client, attempt):
        """Accept only this attempt, never an older preflight or reply."""
        with self._lock:
            if attempt != self._generation:
                raise FeedError("Device sign-in was cancelled")
        reader = login_client.login()
        if type(reader) is not V2ReadonlyHTTPSReader:
            raise FeedError("Approved read-only device session required")
        with self._lock:
            if attempt != self._generation:
                reader.invalidate()
                raise FeedError("Device sign-in was cancelled")
            self._reader = reader
        return True

    def sign_in(self, login_client):
        """Accept only a successful signed HTTPS login, never a token string."""
        if type(login_client) is not V2P256LoginHTTPSClient:
            raise FeedError("Approved P-256 HTTPS login client required")
        return self._complete_sign_in(login_client, self._begin_sign_in())

    def sign_in_with_keystore(self, binding, approved_https_origin, *,
                              opener=None, timeout=10):
        """Reserve BEFORE native public-key preflight to honor logout.

        No Android implementation bundled. Server enrollment remains required.
        Refuse generic signers, user-supplied bearer and untrusted binding type.
        """
        if type(binding) is not AndroidKeystoreLoginBinding:
            raise FeedError("Approved Android Keystore login binding required")
        attempt = self._begin_sign_in()
        client = binding.login_client(
            approved_https_origin, opener=opener, timeout=timeout)
        return self._complete_sign_in(client, attempt)

    def active_reader(self):
        with self._lock:
            reader = self._reader
            if reader is None or not reader.session_active:
                raise FeedError("V2 device session sign-in required")
            return reader
