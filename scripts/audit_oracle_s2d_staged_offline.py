"""Offline-only proof of the Oracle staged S2D quote gate.

Loads a proposed Python module by path with fake credentials and a fake opener.
Never opens a socket, reads Oracle config/token files, or alters the production adapter.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import time
import urllib.error

EXPECTED_SHA = "beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c"
DEFAULT = "/opt/bot-king-backups/s2d-stage/dhan_feed.s2d.proposed.20261116T031325151738Z.py"

class FakeResponse:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size):
        return b'{"data":{}}'

def main(path):
    candidate = Path(path)
    if not candidate.is_file() or candidate.is_symlink():
        raise RuntimeError("Expected regular staged file, not production or symlink")
    if candidate.resolve() == Path("/opt/bot-king-server/dhan_feed.py"):
        raise RuntimeError("Refusing live production path")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA:
        raise RuntimeError("Stage hash mismatch; refuse unreviewed source")
    spec = importlib.util.spec_from_file_location("botking_s2d_staged_offline", str(candidate))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    starts = []
    def fake_opener(request, timeout):
        assert request.full_url.endswith("/marketfeed/ltp"), request.full_url
        starts.append(time.monotonic())
        return FakeResponse()
    first = module.DhanFeed("offline-test-id", "offline-test-token", opener=fake_opener)
    second = module.DhanFeed("offline-test-id", "offline-test-token", opener=fake_opener)
    first.ltp("NSE_EQ", 2885)
    second.ltp("NSE_EQ", 2885)
    assert len(starts) == 2, starts
    gap = starts[1] - starts[0]
    assert gap >= 1.04, "Quote gap below 1.04 seconds: %.5f" % gap
    # Test the actual staged module's HTTP429 guard without a network call.
    def throttled(*args, **kwargs):
        raise urllib.error.HTTPError("fake://no-network", 429, "rate limited", {}, None)
    module.DhanFeed._retry_after = 0.0
    limited = module.DhanFeed("offline-test-id", "offline-test-token", opener=throttled)
    try:
        limited.ltp("NSE_EQ", 2885)
    except module.DhanRateLimitError:
        pass
    else:
        raise AssertionError("Fake 429 did not raise rate-limit error")
    prior = len(starts)
    try:
        first.ltp("NSE_EQ", 2885)
    except module.DhanRateLimitError:
        pass
    else:
        raise AssertionError("429 cooldown was not shared across instances")
    assert len(starts) == prior, "A call bypassed the shared 429 cooldown"
    assert all(hasattr(module.DhanFeed, k) for k in (
        "_historical_retry_after", "_option_retry_after", "_intraday_next_allowed"
    )), "Oracle-specific existing cooldowns must be preserved"
    print("S2D_OFFLINE_BEHAVIOR_PASS: YES")
    print("STAGED_SHA256:", digest)
    print("QUOTES_TESTED: 2 fake opener calls across 2 instances")
    print("QUOTE_START_GAP_SECONDS: %.3f" % gap)
    print("429_SHARED_COOLDOWN: PASS")
    print("ORACLE_HISTORICAL_OPTION_FIELDS: PRESENT")
    print("NETWORK_REQUESTS: 0")
    print("PRODUCTION_CHANGED: NO")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged-file", default=DEFAULT)
    args = parser.parse_args()
    main(args.staged_file)
