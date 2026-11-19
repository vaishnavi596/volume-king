"""V2 optional device P-256 challenge/login HTTPS client; NOT wired to main.

A separate, trusted Android Keystore adapter must supply sign_p256_message.
Never load, create, export, print, persist, or transmit a private key here.
Only the server can verify the signed challenge and authorize device feeds.
"""
import base64
import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, HTTPSHandler, build_opener
from secure_https_reader import (
    FeedError, V2ReadonlyHTTPSReader, _NoRedirects, _checked_origin,
)

LOGIN_CONTEXT = b"BOT-KING-V2-DEVICE-LOGIN\x00"
MAX_AUTH_RESPONSE_BYTES = 4096


def _device_id_ok(value):
    return (type(value) is str and 16 <= len(value) <= 128 and
            all(ch.isascii() and (ch.isalnum() or ch in "-_")
                for ch in value))


def _decode_challenge(value):
    if (type(value) is not str or not 1 <= len(value) <= 48 or
            any(ch not in
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
                for ch in value)):
        raise FeedError("Invalid device challenge")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error):
        raise FeedError("Invalid device challenge") from None
    if len(decoded) != 32 or base64.urlsafe_b64encode(decoded).decode(
            "ascii").rstrip("=") != value:
        raise FeedError("Invalid device challenge")
    return decoded


class V2P256LoginHTTPSClient:
    """Explicit signed login only. No automatic retries or broker calls."""

    def __init__(self, trusted_origin, device_id, sign_p256_message, *,
                 opener=None, timeout=10):
        self._origin = _checked_origin(trusted_origin)
        if not _device_id_ok(device_id) or not callable(sign_p256_message):
            raise FeedError("Approved device identity and signer required")
        if type(timeout) not in (int, float) or not 1 <= timeout <= 30:
            raise FeedError("Invalid login request timeout")
        self._device_id = device_id
        self._signer = sign_p256_message
        self._timeout = timeout
        self._opener = (opener if opener is not None else build_opener(
            ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirects()))
        if not callable(getattr(self._opener, "open", None)):
            raise FeedError("Invalid verified HTTPS login opener")

    def _post_json(self, endpoint, payload, exact_keys):
        url = self._origin + endpoint
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(body) > 1024:
            raise FeedError("Login body too large")
        request = Request(url, data=body, method="POST", headers={
            "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                if response.geturl() != url or response.status != 200:
                    raise FeedError("Trusted device login unavailable")
                if response.headers.get_content_type() != "application/json":
                    raise FeedError("Invalid device login response type")
                if response.headers.get("Cache-Control", "").lower() != "no-store":
                    raise FeedError("Device login response may be cached")
                content = response.read(MAX_AUTH_RESPONSE_BYTES + 1)
                if len(content) > MAX_AUTH_RESPONSE_BYTES:
                    raise FeedError("Device login response too large")
                parsed = json.loads(content.decode("utf-8"))
        except (HTTPError, URLError, OSError, UnicodeError, ValueError,
                json.JSONDecodeError):
            raise FeedError("V2 device login unavailable") from None
        if type(parsed) is not dict or set(parsed) != exact_keys:
            raise FeedError("Invalid device login response")
        return parsed

    def login(self):
        """Return only a read-only HTTPS reader; never return/log bearer text."""
        challenge = self._post_json(
            "/v2-pilot/auth/challenge",
            {"device_id": self._device_id}, {"challenge"})["challenge"]
        raw = _decode_challenge(challenge)
        signed_message = (LOGIN_CONTEXT + self._device_id.encode("ascii") +
                          b"\x00" + raw)
        try:
            signature = self._signer(signed_message)
        except Exception:
            # A Keystore error must never expose key aliases or exception data.
            raise FeedError("Approved device signature unavailable") from None
        if type(signature) is not bytes or not 8 <= len(signature) <= 300:
            raise FeedError("Invalid approved device signature")
        signature_text = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        result = self._post_json(
            "/v2-pilot/auth/login",
            {"device_id": self._device_id, "challenge": challenge,
             "signature": signature_text}, {"device_bearer"})
        return V2ReadonlyHTTPSReader(
            self._origin, result["device_bearer"],
            opener=self._opener, timeout=self._timeout)
