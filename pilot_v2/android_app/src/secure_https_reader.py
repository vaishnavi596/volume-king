"""FT-2 V2 bounded HTTPS read-only quote transport.

Not an Android login or a live Oracle integration. The real calling app must
first receive a revocable device bearer from a verified owner-approved P-256
login over an independently trusted server origin. Never persist broker keys.
"""
import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener,
)
from feed_inbox import DeviceFeedInbox, FeedError
from read_delivery import deliver_readonly_response

MAX_RESPONSE_BYTES = 65536


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _checked_origin(value):
    if type(value) is not str or not value or value != value.strip():
        raise FeedError("Master-approved HTTPS origin required")
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Invalid port raises ValueError.
    except ValueError:
        raise FeedError("Invalid trusted HTTPS origin") from None
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
            or not parsed.netloc or port == 0):
        raise FeedError("Invalid trusted HTTPS origin")
    return "https://" + parsed.netloc.rstrip("/")


class V2ReadonlyHTTPSReader:
    """Get only the two protected, versioned feeds using TLS-verifying opener.

    The optional opener is for dependency-injected OFFLINE tests. Providing a
    bearer is not proof of device registration; server checks it each request.
    """

    def __init__(self, trusted_origin, device_bearer, *, opener=None, timeout=10):
        self._origin = _checked_origin(trusted_origin)
        if (type(device_bearer) is not str or not 24 <= len(device_bearer) <= 4096
                or any(not (33 <= ord(char) <= 126) for char in device_bearer)):
            raise FeedError("Valid in-memory device session required")
        if type(timeout) not in (int, float) or not 1 <= timeout <= 30:
            raise FeedError("Invalid HTTPS request timeout")
        self._bearer = device_bearer  # Never printed, persisted or exposed.
        self._timeout = timeout
        self._opener = (opener if opener is not None else build_opener(
            ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirects()))
        if not callable(getattr(self._opener, "open", None)):
            raise FeedError("Invalid verified HTTPS opener")

    @property
    def session_active(self):
        """Only local bearer availability; NOT proof of ongoing server login."""
        return self._bearer is not None

    def invalidate(self):
        """Forget a revoked/expired in-memory session; never persist credentials."""
        self._bearer = None

    def refresh(self, inbox, feed, *, selected_equities=()):
        if not isinstance(inbox, DeviceFeedInbox) or type(feed) is not str or feed not in (
                "quotes", "indices"):
            raise FeedError("Unsupported V2 read-only destination")
        if not self.session_active:
            raise FeedError("V2 device session requires verified sign-in")
        # No Dhan OAuth/broker secret ever goes to this phone.
        url = self._origin + "/v2-pilot/" + feed
        request = Request(
            url, headers={"Authorization": "Bearer " + self._bearer,
                          "Accept": "application/json"}, method="GET")
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                # HTTPSHandler verifies system CA and hostname, and redirects
                # are explicitly disabled for the production opener.
                if response.geturl() != url or response.status != 200:
                    raise FeedError("Untrusted HTTP redirect or response")
                if response.headers.get_content_type() != "application/json":
                    raise FeedError("Unexpected read-only media type")
                content = response.read(MAX_RESPONSE_BYTES + 1)
                if len(content) > MAX_RESPONSE_BYTES:
                    raise FeedError("Oversized read-only response")
                payload = json.loads(content.decode("utf-8"))
        except HTTPError as exc:
            # Only explicit auth rejection invalidates this device session.
            # 429/cooldown or upstream 5xx must NOT erase local auth state.
            if exc.code in (401, 403):
                self.invalidate()
                raise FeedError("V2 device sign-in required; cached data retained") from None
            raise FeedError("V2 HTTPS feed unavailable; cached data retained") from None
        except (URLError, OSError, UnicodeError, ValueError,
                json.JSONDecodeError):
            # Never include upstream exception text: it can contain the URL,
            # bearer, response body or an untrusted server message.
            raise FeedError("V2 HTTPS feed unavailable; cached data retained") from None
        # Only a successful HTTPS response from the configured origin and
        # protected endpoint can enter the independent app-owned lane.
        accepted = deliver_readonly_response(
            inbox, feed, 200, payload, selected_equities=selected_equities,
            authenticated_session=True)
        # Advancing a global envelope without any newer per-symbol row is not
        # a visible data refresh. Do not report HIST or trigger a visual update.
        return bool(accepted and inbox.changed_for(feed))
