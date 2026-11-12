"""BOT KING 226 optional device login transport; not wired into the app.

Uses HTTPS-only, no redirects/proxies, bounded JSON, no credential logging.
Requires an Android native signing bridge before use on a real device.
"""
import base64
import json
import urllib.error
import urllib.request

from server_feed import NoRedirect, server_origin


class OracleDeviceLoginError(RuntimeError):
    pass


class OracleDeviceLogin226:
    def __init__(self, origin, opener=None):
        self.origin = server_origin(origin)
        self._opener = opener or urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )

    def _post(self, path, data):
        req = urllib.request.Request(
            self.origin + path,
            data=json.dumps(data, separators=(",", ":")).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(req, timeout=15) as response:
                if response.status != 200:
                    raise OracleDeviceLoginError("Device authentication unavailable")
                payload = response.read(4097)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise OracleDeviceLoginError("Device authentication request failed") from exc
        if len(payload) > 4096:
            raise OracleDeviceLoginError("Device authentication response too large")
        try:
            result = json.loads(payload)
        except (ValueError, UnicodeDecodeError) as exc:
            raise OracleDeviceLoginError("Invalid device authentication response") from exc
        if not isinstance(result, dict):
            raise OracleDeviceLoginError("Invalid device authentication response")
        return result

    async def login(self, device_id, native_bridge):
        if (not isinstance(device_id, str) or not 16 <= len(device_id) <= 128
                or not all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in device_id)):
            raise OracleDeviceLoginError("Invalid device ID")
        response = self._post("/v2/device/challenge", {"device_id": device_id})
        challenge = response.get("challenge")
        if not isinstance(challenge, str) or len(challenge) != 44:
            raise OracleDeviceLoginError("Invalid server challenge")
        try:
            challenge_bytes = base64.b64decode(challenge, altchars=b"-_", validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise OracleDeviceLoginError("Invalid server challenge") from exc
        if len(challenge_bytes) != 32 or base64.urlsafe_b64encode(challenge_bytes).decode("ascii") != challenge:
            raise OracleDeviceLoginError("Invalid server challenge")
        signature = await native_bridge.sign_login_challenge(device_id, challenge)
        session = self._post("/v2/device/session", {
            "device_id": device_id, "challenge": challenge, "signature": signature
        })
        token = session.get("access_token")
        if (not isinstance(token, str) or not 32 <= len(token) <= 256
                or not token.isascii() or any(ch.isspace() for ch in token)
                or session.get("token_type") != "bearer"
                or type(session.get("expires_in_seconds")) is not int
                or not 0 < session["expires_in_seconds"] <= 900):
            raise OracleDeviceLoginError("Invalid server session response")
        return token
