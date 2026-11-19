"""Single app-owned, in-memory trusted P-256 sign-in reader slot.

No user-entered bearer, fake role, persisted token or auto-login. Actual P-256
signature still requires a separately reviewed Android Keystore callback.
The server independently checks device proof and scope on each read.
"""
from threading import Lock
from app_p256_login import V2P256LoginHTTPSClient
from app_keystore_login_binding import AndroidKeystoreLoginBinding
from secure_https_reader import FeedError, V2ReadonlyHTTPSReader, _checked_origin


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

    def _begin_sign_in(self, *, preserve_previous=False):
        """Reserve a cancellable attempt before any platform/network work.

        During an approved Keystore re-login the old signed session remains
        usable until a new verified reader is accepted or the owner clears it.
        Direct generic client replacement retains its previous scrub rule.
        """
        with self._lock:
            self._generation += 1
            attempt = self._generation
            if preserve_previous:
                previous = None
            else:
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
        if type(reader) is not V2ReadonlyHTTPSReader or not reader.session_active:
            raise FeedError("Active read-only device session required")
        # Keep the acceptance, alias and cancellation checks together.
        # A buggy login provider may return the SAME reader already retained
        # by this slot; never scrub that good reader as a rejected "new" one.
        with self._lock:
            if reader is self._reader:
                raise FeedError("New signed device session required")
            if attempt != self._generation:
                reader.invalidate()
                raise FeedError("Device sign-in was cancelled")
            # Refuse a reader from a different origin before handover.
            if reader._origin != login_client._origin:
                reader.invalidate()
                raise FeedError("Signed device session origin mismatch")
            if not reader.session_active:
                raise FeedError("Active read-only device session required")
            previous, self._reader = self._reader, reader
            # Complete the handover before exposing the new session.
            # Do not hold this lock during HTTPS I/O; invalidate a previous
            # reader while serialized with other local session operations.
            if previous is not None and previous is not reader:
                previous.invalidate()
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
        # Reject static caller mistakes without evicting a usable session.
        # The native public key check itself remains behind the generation
        # reservation so clear() can cancel a slow platform callback.
        trusted_origin = _checked_origin(approved_https_origin)
        if type(timeout) not in (int, float) or not 1 <= timeout <= 30:
            raise FeedError("Invalid login request timeout")
        # Validate an injected HTTPS opener before disrupting a valid reader.
        # Runtime production uses the client's own TLS-verifying opener.
        if opener is not None:
            try:
                valid_opener = callable(getattr(opener, "open", None))
            except Exception:
                valid_opener = False
            if not valid_opener:
                raise FeedError("Invalid verified HTTPS login opener")
        attempt = self._begin_sign_in(preserve_previous=True)
        client = binding.login_client(
            trusted_origin, opener=opener, timeout=timeout)
        return self._complete_sign_in(client, attempt)

    def active_reader(self):
        with self._lock:
            reader = self._reader
            if reader is None or not reader.session_active:
                raise FeedError("V2 device session sign-in required")
            return reader
