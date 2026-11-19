"""Authenticated V2 evidence delivery into the existing atomic app-owned caches.

This is an optional client contract for the future protected Oracle
/v2-pilot/evidence endpoint. A 404 or absent provider is WAIT, not LIVE.
No direct Dhan requests, refresh timers, fake candles, or new source signals.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request

from app_evidence_batch import apply_staged_evidence_batch, EvidenceBatchError
from evidence_inbox import DeviceEvidenceInbox
from secure_https_reader import V2ReadonlyHTTPSReader
from feed_inbox import FeedError

MAX_EVIDENCE_BYTES = 65536


def read_signed_evidence_batch(reader, inbox, *, selected_equities):
    """Only an existing signed HTTPS reader may ingest an atomic evidence batch.

    The bearer remains in memory, and is rechecked after I/O so a concurrent
    logout/relogin cannot publish a stale HTTP response to the current cache.
    The endpoint must independently enforce device scope and Dhan provenance.
    """
    if type(reader) is not V2ReadonlyHTTPSReader:
        raise FeedError("Approved signed V2 reader required")
    if type(inbox) is not DeviceEvidenceInbox:
        raise FeedError("Approved V2 evidence cache required")
    if type(selected_equities) not in (list, tuple):
        raise FeedError("Invalid selected equity roster")
    selected = tuple(selected_equities)
    try:
        inbox.allowed(selected)
    except (ValueError, TypeError):
        raise FeedError("Invalid selected equity roster") from None

    with reader._session_lock:
        bearer = reader._bearer
        if bearer is None:
            raise FeedError("V2 device sign-in required")
    url = reader._origin + "/v2-pilot/evidence"
    request = Request(url, method="GET", headers={
        "Authorization": "Bearer " + bearer,
        "Accept": "application/json",
        "Cache-Control": "no-store",
    })
    try:
        with reader._opener.open(request, timeout=reader._timeout) as response:
            if response.status != 200 or response.geturl() != url:
                raise FeedError("Authenticated V2 evidence unavailable")
            if response.headers.get_content_type() != "application/json":
                raise FeedError("Invalid authenticated evidence content type")
            if response.headers.get("Cache-Control", "").lower() != "no-store":
                raise FeedError("Evidence response may be cached")
            data = response.read(MAX_EVIDENCE_BYTES + 1)
            if len(data) > MAX_EVIDENCE_BYTES:
                raise FeedError("Evidence response exceeds safe size")
            decoded = json.loads(data.decode("utf-8"))
    except HTTPError as exc:
        if exc.code in (401, 403):
            reader.invalidate()
            raise FeedError("V2 device sign-in required") from None
        raise FeedError("Authenticated V2 evidence unavailable") from None
    except (URLError, OSError, UnicodeError, ValueError, TypeError):
        raise FeedError("Authenticated V2 evidence unavailable") from None

    if type(decoded) is not dict or set(decoded) != {"events"}:
        raise FeedError("Invalid authenticated evidence envelope")
    with reader._session_lock:
        if reader._bearer != bearer:
            raise FeedError("V2 session changed during evidence delivery")
        # Atomic staging and final publication serialize with sign-out.
        try:
            return apply_staged_evidence_batch(
                inbox, decoded["events"], selected_equities=selected,
                trusted_transport=True)
        except (EvidenceBatchError, ValueError, TypeError):
            raise FeedError("Untrusted V2 source evidence rejected") from None
