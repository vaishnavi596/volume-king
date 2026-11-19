"""Offline tests for protected Oracle Dhan expiry source; no real Dhan/Oracle traffic."""
import json
import unittest
from urllib.error import HTTPError

from pilot_v2.oracle_dhan_expiry_transport import OracleDhanExpiryTransport
from pilot_v2.oracle_evidence_lane import OracleDhanEvidenceLane
from pilot_v2.shared_read_budget import SharedReadBudget
from pilot_v2.internal_dhan_read_port import DhanRateLimited, DhanReadUnavailable
from pilot_v2.unified_data_pipeline import PipelineUnavailable

URL = "http://127.0.0.1:8000/dhan/option-expiries"
KEY = "a-private-synthetic-pairing-key-000000000000"


class Reply:
    status = 200
    def __init__(self, obj, url=URL):
        self._raw = json.dumps(obj).encode("utf-8")
        self._url = url
    def __enter__(self):
        return self
    def __exit__(self, *unused):
        pass
    def geturl(self):
        return self._url
    def read(self, length):
        return self._raw[:length]


class FakeOpener:
    def __init__(self, payload, error=None, url=URL):
        self.payload = payload
        self.error = error
        self.url = url
        self.calls = []
    def open(self, request, timeout):
        self.calls.append(request)
        if self.error:
            raise self.error
        return Reply(self.payload, self.url)


def good():
    return {"source": "dhan", "symbol": "NIFTY",
            "expiries": ["2026-12-03", "2026-11-26"],
            "live_orders_enabled": False}


class PrivateDhanExpiryContractTests(unittest.TestCase):
    def test_protected_loopback_and_canonical_sorted_expiry(self):
        opener = FakeOpener(good())
        transport = OracleDhanExpiryTransport(
            pairing_key=KEY, symbol="NIFTY", opener=opener,
            clock=lambda: 1800000000)
        result = transport()
        self.assertEqual(result.source, "dhan")
        self.assertEqual(result.revision, 1)
        self.assertEqual(result.events, [{
            "kind": "expiries", "symbol": "NIFTY", "revision": 1,
            "available": ["2026-11-26", "2026-12-03"]}])
        request = opener.calls[0]
        self.assertEqual(request.full_url, URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("X-botking-key"), KEY)
        self.assertEqual(json.loads(request.data), {"symbol": "NIFTY"})
        self.assertEqual(transport().revision, 2)
        self.assertEqual(len(opener.calls), 2)  # One HTTP per explicit call.

    def test_bogus_source_bad_expiry_redirect_and_no_private_fallback(self):
        bad = (
            dict(good(), source="mock"),
            dict(good(), symbol="RELIANCE"),
            dict(good(), live_orders_enabled=True),
            dict(good(), expiries=[]),
            dict(good(), expiries=["2026-02-30"]),
            dict(good(), expiries=["2026-11-26", "2026-11-26"]),
            dict(good(), expiries=["2026-11-26"] * 65),
            dict(good(), expiries=[True]),
        )
        for item in bad:
            with self.subTest(bad=str(item)[:60]):
                bridge = OracleDhanExpiryTransport(
                    pairing_key=KEY, symbol="NIFTY",
                    opener=FakeOpener(item), clock=lambda: 1800000000)
                with self.assertRaises(DhanReadUnavailable):
                    bridge()
                self.assertEqual(bridge._revision, 0)
        opener = FakeOpener(good(), url="http://untrusted.example/redirect")
        bridge = OracleDhanExpiryTransport(
            pairing_key=KEY, symbol="NIFTY", opener=opener)
        with self.assertRaises(DhanReadUnavailable):
            bridge()
        for invalid in ("", "lower", "SYMBOL/../X", None):
            with self.assertRaises(ValueError):
                OracleDhanExpiryTransport(pairing_key=KEY, symbol=invalid)

    def test_429_cooldown_shared_with_quotes_and_no_retry(self):
        opener = FakeOpener(good(), error=HTTPError(URL, 429, "rate-limit", {}, None))
        transport = OracleDhanExpiryTransport(
            pairing_key=KEY, symbol="NIFTY", opener=opener)
        with self.assertRaises(DhanRateLimited):
            transport()
        ticks = [100.0]
        budget = SharedReadBudget(monotonic=lambda: ticks[0])
        lane = OracleDhanEvidenceLane(
            transport=transport, read_budget=budget,
            monotonic=lambda: ticks[0], clock=lambda: 1800000000)
        with self.assertRaises(PipelineUnavailable):
            lane("approved-device")
        self.assertEqual(budget.status()["cooldown_seconds"], 30.0)
        with self.assertRaises(PipelineUnavailable):
            lane("approved-device")
        self.assertEqual(len(opener.calls), 2)  # No additional request on cooldown.

    def test_real_private_bridge_to_bounded_evidence_lane_contract(self):
        opener = FakeOpener(good())
        bridge = OracleDhanExpiryTransport(
            pairing_key=KEY, symbol="NIFTY", opener=opener,
            clock=lambda: 1800000000)
        ticks = [100.0]
        lane = OracleDhanEvidenceLane(
            transport=bridge,
            read_budget=SharedReadBudget(monotonic=lambda: ticks[0]),
            monotonic=lambda: ticks[0], clock=lambda: 1800000000)
        result = lane("approved-device")
        self.assertEqual(result["events"][0]["available"],
                         ["2026-11-26", "2026-12-03"])
        result["events"][0]["symbol"] = "TAMPER"
        self.assertEqual(lane("other-approved-device")["events"][0]["symbol"],
                         "NIFTY")
        self.assertEqual(len(opener.calls), 1)
        ticks[0] += 31
        self.assertEqual(lane("approved-device")["events"][0]["revision"], 2)
        self.assertEqual(len(opener.calls), 2)


if __name__ == "__main__":
    unittest.main()
