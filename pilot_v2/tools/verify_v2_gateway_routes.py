#!/usr/bin/env python3
"""LIVE-MVP-01 Gate 1: no-auth read-only route reconnaissance, NOT deployment proof.

Never sends tokens, POST requests, private keys or broker orders; never reads
response bodies. 401/403/405 alone may be an edge-proxy response, not a route.
"""
import argparse
import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener,
)

# GET-only no-auth check: do NOT infer POST route status from GET 404.
PATHS = (
    "/health",
    "/v2-pilot/health",
    "/v2-pilot/indices",
    "/v2-pilot/quotes",
    "/v2-pilot/private-backup",
)
POST_ONLY_NOT_TESTED = (
    "/v2-pilot/auth/challenge",
    "/v2-pilot/auth/login",
)


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _origin(value):
    if not isinstance(value, str) or value != value.strip():
        raise ValueError("HTTPS origin required")
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid HTTPS origin") from None
    if (parsed.scheme != "https" or not parsed.hostname or not parsed.netloc
            or parsed.username or parsed.password or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment or port == 0):
        raise ValueError("Trusted HTTPS origin only; no path or credentials")
    return "https://" + parsed.netloc.rstrip("/")


def _meaning(code):
    if code == 404:
        return "NOT_FOUND_AT_PUBLIC_EDGE"
    if code in (401, 403):
        return "AUTH_DENIED_ROUTE_UNCONFIRMED"
    if code == 405:
        return "METHOD_DENIED_ROUTE_UNCONFIRMED"
    if code == 200:
        return "PUBLIC_200_NOT_AUTH_OR_DATA_PROOF"
    if 300 <= code < 400:
        return "REDIRECT_REJECTED"
    return "INCONCLUSIVE"


def probe(origin, *, opener, timeout=5):
    """No-auth GET-only edge check; inspect status, NEVER read response body."""
    if (type(timeout) not in (int, float)
            or not 1 <= timeout <= 15):
        raise ValueError("Timeout must be 1–15 seconds")
    origin = _origin(origin)
    outcomes = []
    for path in PATHS:
        url = origin + path
        req = Request(url, method="GET", headers={"Accept": "application/json"})
        try:
            with opener.open(req, timeout=timeout) as response:
                code = response.status
                if response.geturl() != url:
                    outcomes.append({"path": path, "status": None,
                                     "assessment": "REDIRECT_REJECTED"})
                    continue
        except HTTPError as error:
            code = error.code
        except (URLError, OSError, ValueError, TimeoutError):
            outcomes.append({"path": path, "status": None,
                             "assessment": "UNREACHABLE_OR_TLS_ERROR"})
            continue
        outcomes.append({"path": path, "status": code,
                         "assessment": _meaning(code)})
    return {"gate": "LIVE-MVP-01/GATE-1", "status": "OPEN_UNVERIFIED",
            "tests": outcomes, "post_only_not_tested": list(POST_ONLY_NOT_TESTED),
            "limits": "No POST, credentials or bodies; no live/auth proof. GET-only 404 cannot establish a POST endpoint's availability"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True, help="Approved HTTPS origin")
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    try:
        opener = build_opener(ProxyHandler({}),
                              HTTPSHandler(context=ssl.create_default_context()),
                              _NoRedirects())
        result = probe(args.origin, opener=opener, timeout=args.timeout)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
